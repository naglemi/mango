#!/usr/bin/env python3
"""
SLURM Job Selector - Interactive menu for connecting to running SLURM jobs
Fetches jobs from Expanse and provides interactive selection
"""

import os
import sys
import termios
import tty
import subprocess
import pexpect
import time
from pathlib import Path
from typing import List, Tuple, Optional

class SlurmJobSelector:
    """Interactive SLURM job selector."""

    def __init__(self):
        self.jobs = []
        self.current_selection = 0
        self.loading = True

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='', flush=True)

    def _display_loading(self):
        """Display loading screen."""
        self._clear_screen()
        print(" SLURM Job Selector")
        print("=" * 50)
        print()
        print("Connecting to Expanse and fetching your jobs...")
        print("This may take up to 30 seconds...")
        print()
        print("Press 'q' to cancel")

    def _fetch_jobs(self) -> List[Tuple[str, str, str]]:
        """Fetch SLURM jobs from Expanse."""
        jobs = []

        try:
            # Generate TOTP
            result = subprocess.run(['oathtool', '--totp=SHA1', '--base32', 'AJW3D7MUBZGYE2B6SK6V6NCFL3S4Q2SV'],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(" Failed to generate TOTP code")
                return jobs

            totp_code = result.stdout.strip()
            ssh_key = os.path.expanduser('~/.ssh/id_rsa_expanse')

            # Connect to Expanse
            cmd = f'ssh -i {ssh_key} -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ControlMaster=no -o ControlPath=none naglemi@login.expanse.sdsc.edu'
            child = pexpect.spawn(cmd)
            child.timeout = 30

            # Handle TOTP
            child.expect(r'.*TOTP code for naglemi:.*')
            child.sendline(totp_code)

            # Wait for MOTD to finish
            child.expect(r'.*adjust your environment:.*')
            time.sleep(1)

            # Get fresh prompt and run command
            child.sendline('')
            time.sleep(0.5)
            child.sendline('sacct -u naglemi --state=RUNNING --format=JobID,JobName,NodeList --noheader')

            # Wait for command completion
            time.sleep(3)
            child.expect(r'.*naglemi@.*')

            # Get output
            output = child.before.decode('utf-8')
            child.sendline('exit')
            child.close()

            # Parse job lines
            for line in output.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    # Skip batch/extern sub-jobs
                    if '.batch' in line or '.extern' in line:
                        continue

                    parts = line.split()
                    if len(parts) >= 3:
                        job_id = parts[0]
                        job_name = parts[1]
                        node_list = parts[2]

                        if node_list != "None" and node_list:
                            jobs.append((job_id, job_name, node_list))

        except pexpect.exceptions.TIMEOUT:
            print(" Connection to Expanse timed out")
            print("This might be due to:")
            print("  - Network connectivity issues")
            print("  - Expanse being down for maintenance")
            print("  - SSH key or TOTP issues")
        except Exception as e:
            print(f" Error fetching jobs: {e}")

        return jobs

    def _display_menu(self):
        """Display the job selection menu."""
        self._clear_screen()

        print(" SLURM Job Selector")
        print("=" * 50)
        print("Controls: ↑↓/WS navigate, ENTER connect, q quit")
        print("=" * 50)
        print()

        if not self.jobs:
            print(" No running SLURM jobs found")
            print()
            print("This could mean:")
            print("  • No jobs are currently running")
            print("  • Jobs haven't started yet (still queued)")
            print("  • Connection to Expanse failed")
            print()
            print("Press 'q' to exit")
            return

        # Display jobs
        for i, (job_id, job_name, node_list) in enumerate(self.jobs):
            if i == self.current_selection:
                print(f"> Job {job_id}: {job_name} on {node_list}")
            else:
                print(f"  Job {job_id}: {job_name} on {node_list}")

        print()
        print(f"Found {len(self.jobs)} running jobs")

    def _get_char(self) -> str:
        """Get a single character from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

            # Handle arrow keys
            if ch == '\033':
                ch += sys.stdin.read(1)
                if ch == '\033[':
                    ch += sys.stdin.read(1)

            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _handle_input(self, key: str) -> bool:
        """Handle keyboard input. Returns False to exit."""
        if key in ['q', 'Q']:
            return False

        if not self.jobs:
            return True  # Only allow quit if no jobs

        if key == '\033[A' or key == 'w' or key == 'W':  # Up
            self.current_selection = max(0, self.current_selection - 1)
        elif key == '\033[B' or key == 's' or key == 'S':  # Down
            self.current_selection = min(len(self.jobs) - 1, self.current_selection + 1)
        elif key == '\r' or key == '\n':  # Enter
            return self._connect_to_job()

        return True

    def _connect_to_job(self) -> bool:
        """Connect to the selected job's node."""
        if 0 <= self.current_selection < len(self.jobs):
            job_id, job_name, node_list = self.jobs[self.current_selection]

            # Handle node list (might be like "exp-8-60" or multiple nodes)
            node = node_list.split(',')[0]  # Take first node if multiple

            print(f"\n Connecting to {node} (Job {job_id}: {job_name})...")

            try:
                # Use the SSH wrapper for TOTP handling
                ssh_wrapper = Path.home() / 'mango' / 'auth' / 'ssh-wrapper'
                if ssh_wrapper.exists():
                    subprocess.run([str(ssh_wrapper), node])
                else:
                    subprocess.run(['ssh', node])
            except KeyboardInterrupt:
                print("\n  Connection interrupted")
            except Exception as e:
                print(f"\n SSH connection failed: {e}")
                input("Press Enter to continue...")
                return True

        return False

    def run_menu(self):
        """Run the interactive SLURM job selector."""
        try:
            # Show loading screen and fetch jobs
            self._display_loading()
            self.jobs = self._fetch_jobs()

            # Show results menu
            while True:
                self._display_menu()
                key = self._get_char()
                if not self._handle_input(key):
                    break

        except KeyboardInterrupt:
            print("\n SLURM job selector closed.")

def main():
    """Main entry point."""
    try:
        selector = SlurmJobSelector()
        selector.run_menu()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()