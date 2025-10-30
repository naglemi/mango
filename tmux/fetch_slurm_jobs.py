#!/usr/bin/env python3
import pexpect
import os
import sys
import time

# Generate TOTP
totp_code = os.popen('oathtool --totp=SHA1 --base32 "AJW3D7MUBZGYE2B6SK6V6NCFL3S4Q2SV" 2>/dev/null').read().strip()
ssh_key = os.path.expanduser('~/.ssh/id_rsa_expanse')

try:
    # Spawn SSH connection
    child = pexpect.spawn(f'ssh -i {ssh_key} -o StrictHostKeyChecking=no -o ControlMaster=no -o ControlPath=none naglemi@login.expanse.sdsc.edu')
    child.timeout = 30

    # Wait for TOTP prompt and send code
    child.expect(r'.*TOTP code for naglemi:.*')
    child.sendline(totp_code)

    # Wait for the MOTD to finish (look for the "adjust your environment" text)
    child.expect(r'.*adjust your environment:.*')

    # Wait a bit for the prompt to appear
    time.sleep(2)

    # Send a newline to get a fresh prompt, then the sacct command
    child.sendline('')
    time.sleep(0.5)
    child.sendline('sacct -u naglemi --state=RUNNING --format=JobID,JobName,NodeList --noheader')

    # Wait for the command to complete (look for any naglemi@ prompt)
    time.sleep(2)
    child.expect(r'.*naglemi@.*')

    # Get the output
    output = child.before.decode('utf-8')

    # Send exit
    child.sendline('exit')
    child.close()

    # Print the output for bash to capture
    print(output)

except pexpect.exceptions.TIMEOUT:
    print("TIMEOUT: Failed to connect or execute command", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)