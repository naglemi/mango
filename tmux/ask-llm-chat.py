#!/usr/bin/env python3
"""
Ask LLM Interactive Chat - Core chat interface with Q to quit, A to ask follow-up
Handles real-time display, MCP tool integration, and session management
"""

import os
import sys
import json
import subprocess
import termios
import tty
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ask_llm_output_manager import AskLLMOutputManager

class AskLLMChat:
    """Interactive chat system with LLM models via MCP tools."""

    def __init__(self, models: List[Tuple[str, str]], comparison_mode: bool = False):
        """
        Initialize chat with selected models.
        models: List of (model_name, mcp_tool_name) tuples
        """
        self.models = models
        self.comparison_mode = comparison_mode
        self.output_manager = AskLLMOutputManager()
        self.session_files = {}  # model_name -> (timestamped_path, latest_path)
        self.comparison_file = None

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _display_header(self, question: str):
        """Display chat session header."""
        self._clear_screen()
        print(" Ask LLM - Interactive Chat")
        print("=" * 80)

        if self.comparison_mode:
            model_names = [name.upper() for name, _ in self.models]
            print(f"Models: {', '.join(model_names)} (COMPARISON MODE)")
        else:
            print(f"Models: {', '.join(name.upper() for name, _ in self.models)}")

        print("=" * 80)
        print()
        print("QUESTION:")
        print(question)
        print()
        print("=" * 80)

    def _call_mcp_tool(self, mcp_tool: str, messages: List[Dict]) -> str:
        """Call MCP tool via claude command and return response."""
        try:
            # Prepare the MCP tool call
            tool_call = {
                "tool": mcp_tool,
                "parameters": {
                    "messages": messages
                }
            }

            # Create a temporary script to call claude with the MCP tool
            temp_script = f"""
import json
import sys

# The tool call data
tool_call = {json.dumps(tool_call)}

# Print the tool call in the format Claude expects
print(f"Using MCP tool: {{tool_call['tool']}}")
print("Messages:", json.dumps(tool_call['parameters']['messages'], indent=2))
"""

            # Write to temp file
            temp_file = Path("/tmp/ask_llm_mcp_call.py")
            temp_file.write_text(temp_script)

            # Execute via claude (this is a simplified approach)
            # In practice, we'd need to integrate more directly with Claude's MCP system
            result = subprocess.run([
                "python3", "-c",
                f"""
import subprocess
import json

# Simulate MCP call - in real implementation this would go through Claude's MCP system
# For now, return a placeholder response
messages = {json.dumps(messages)}
print("This would call {mcp_tool} with messages:", json.dumps(messages, indent=2))
print("\\n[Response would appear here from the actual LLM model]")
print("\\nNote: This is a placeholder implementation. Real version would integrate with Claude's MCP system.")
"""
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error calling {mcp_tool}: {result.stderr}"

        except subprocess.TimeoutExpired:
            return f"Timeout calling {mcp_tool}"
        except Exception as e:
            return f"Error calling {mcp_tool}: {e}"

    def _get_user_input(self, prompt: str) -> Optional[str]:
        """Get user input with proper terminal handling."""
        try:
            print(prompt, end='', flush=True)
            return input()
        except (EOFError, KeyboardInterrupt):
            return None

    def _wait_for_action(self) -> str:
        """Wait for user action (Q to quit, A to ask follow-up)."""
        print("\n" + "=" * 80)
        print("Actions: [Q]uit | [A]sk follow-up | Press any other key to continue...")
        print("=" * 80)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1).lower()
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def start_session(self, initial_question: str, files_content: List[Tuple[str, str]] = None,
                     context: List[str] = None) -> bool:
        """
        Start an interactive chat session.
        Returns True if session completed normally, False if cancelled.
        """
        # Prepare initial message with context and files
        message_parts = []

        # Add context if provided
        if context:
            message_parts.append("PREVIOUS CONTEXT:")
            message_parts.extend(context)
            message_parts.append("\n")

        # Add file contents if provided
        if files_content:
            message_parts.append("ATTACHED FILES:")
            for file_path, content in files_content:
                message_parts.append(f"\n===== {file_path} =====")
                message_parts.append(content)
            message_parts.append("\n")

        # Add the actual question
        message_parts.append("QUESTION:")
        message_parts.append(initial_question)

        full_message = "\n".join(message_parts)

        # Initialize session files
        if self.comparison_mode:
            model_names = [name for name, _ in self.models]
            self.comparison_file = self.output_manager.create_comparison_session(
                model_names, initial_question, files_content
            )
        else:
            for model_name, _ in self.models:
                timestamped, latest = self.output_manager.create_session_file(
                    model_name, initial_question, files_content
                )
                self.session_files[model_name] = (timestamped, latest)

        # Start the chat loop
        current_question = initial_question
        conversation_history = []

        while True:
            self._display_header(current_question)

            # Prepare messages for LLM
            messages = [{"role": "user", "content": full_message}]

            if self.comparison_mode:
                # Query all models and display responses side by side
                responses = {}

                for model_name, mcp_tool in self.models:
                    print(f"\n Querying {model_name.upper()}...")
                    response = self._call_mcp_tool(mcp_tool, messages)
                    responses[model_name] = response

                    # Append to comparison file
                    self.output_manager.append_comparison_response(
                        self.comparison_file, model_name, response
                    )

                # Display all responses
                print("\n" + "=" * 80)
                for model_name, response in responses.items():
                    print(f"\n {model_name.upper()} RESPONSE:")
                    print("-" * 40)
                    print(response)

            else:
                # Query models sequentially
                for model_name, mcp_tool in self.models:
                    print(f"\n Querying {model_name.upper()}...")
                    response = self._call_mcp_tool(mcp_tool, messages)

                    print(f"\n {model_name.upper()} RESPONSE:")
                    print("-" * 60)
                    print(response)

                    # Save to individual session files
                    timestamped, latest = self.session_files[model_name]
                    self.output_manager.append_response(timestamped, latest, response)

                    if len(self.models) > 1:
                        print(f"\n{'-' * 60}")

            # Wait for user action
            action = self._wait_for_action()

            if action == 'q':
                print("\n Session ended.")
                return True
            elif action == 'a':
                print()
                follow_up = self._get_user_input("Enter your follow-up question: ")

                if follow_up is None or follow_up.strip() == "":
                    print("No follow-up entered.")
                    continue

                # Add follow-up to session files
                if self.comparison_mode:
                    # For comparison mode, we'd need to extend the comparison file format
                    # For now, create a new comparison session
                    current_question = follow_up
                    full_message = follow_up
                else:
                    for model_name in self.session_files:
                        timestamped, latest = self.session_files[model_name]
                        self.output_manager.append_follow_up_question(
                            timestamped, latest, follow_up
                        )

                current_question = follow_up
                full_message = follow_up

                # Add to conversation history
                conversation_history.append({
                    "question": current_question,
                    "responses": {}  # Would store responses here
                })

            else:
                # Any other key continues/exits
                print("\n Session ended.")
                return True

def main():
    """Main entry point for testing."""
    if len(sys.argv) < 4:
        print("Usage: ask-llm-chat.py <model_name> <mcp_tool> <question> [comparison_mode]")
        sys.exit(1)

    model_name = sys.argv[1]
    mcp_tool = sys.argv[2]
    question = sys.argv[3]
    comparison_mode = len(sys.argv) > 4 and sys.argv[4].lower() == "true"

    models = [(model_name, mcp_tool)]
    chat = AskLLMChat(models, comparison_mode)

    # Test with a simple question
    success = chat.start_session(question)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()