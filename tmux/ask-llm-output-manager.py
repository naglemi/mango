#!/usr/bin/env python3
"""
Ask LLM Output Manager - Handles file output formatting, directory management, and response persistence
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class AskLLMOutputManager:
    """Manages output formatting and file persistence for LLM interactions."""

    def __init__(self, base_dir: str = "/home/ubuntu/mango/ask_llm_outputs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def _ensure_model_dir(self, model_name: str) -> Path:
        """Ensure model directory exists and return path."""
        model_dir = self.base_dir / model_name
        model_dir.mkdir(exist_ok=True)
        return model_dir

    def _get_human_timestamp(self) -> str:
        """Generate human-readable timestamp."""
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _format_file_content(self, files_content: List[Tuple[str, str]]) -> str:
        """Format file contents in ninjagrab style with delimiters."""
        if not files_content:
            return ""

        formatted = []
        formatted.append("=== ATTACHED FILES ===")
        formatted.append("")

        for file_path, content in files_content:
            formatted.append(f"===== {file_path} =====")
            formatted.append(content)
            formatted.append("")

        return "\n".join(formatted)

    def create_session_file(self, model_name: str, question: str, files_content: List[Tuple[str, str]] = None) -> Tuple[Path, Path]:
        """
        Create a new session file for a model.
        Returns: (timestamped_file_path, latest_file_path)
        """
        model_dir = self._ensure_model_dir(model_name)
        timestamp = self._get_human_timestamp()

        # Create file paths
        timestamped_file = model_dir / f"{timestamp}.txt"
        latest_file = model_dir / "latest_response.txt"

        # Format initial content
        content_lines = []
        content_lines.append("=" * 80)
        content_lines.append(f"ASK LLM SESSION - {model_name.upper()}")
        content_lines.append("=" * 80)
        content_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append(f"Model: {model_name}")
        content_lines.append("")

        # Add file contents if provided
        if files_content:
            content_lines.append(self._format_file_content(files_content))
            content_lines.append("")

        # Add initial question
        content_lines.append("=" * 40 + " QUESTION " + "=" * 33)
        content_lines.append(question)
        content_lines.append("")
        content_lines.append("=" * 40 + " RESPONSE " + "=" * 33)
        content_lines.append("")

        # Write initial content to both files
        initial_content = "\n".join(content_lines)
        timestamped_file.write_text(initial_content)
        latest_file.write_text(initial_content)

        return timestamped_file, latest_file

    def append_response(self, timestamped_file: Path, latest_file: Path, response: str):
        """Append a response to both timestamped and latest files."""
        response_content = response + "\n\n"

        # Append to timestamped file
        with open(timestamped_file, 'a') as f:
            f.write(response_content)

        # Overwrite latest file with updated content
        with open(latest_file, 'a') as f:
            f.write(response_content)

    def append_follow_up_question(self, timestamped_file: Path, latest_file: Path, question: str):
        """Append a follow-up question to both files."""
        follow_up_content = []
        follow_up_content.append("=" * 37 + " FOLLOW-UP " + "=" * 32)
        follow_up_content.append(question)
        follow_up_content.append("")
        follow_up_content.append("=" * 40 + " RESPONSE " + "=" * 33)
        follow_up_content.append("")

        follow_up_text = "\n".join(follow_up_content)

        # Append to both files
        with open(timestamped_file, 'a') as f:
            f.write(follow_up_text)

        with open(latest_file, 'a') as f:
            f.write(follow_up_text)

    def create_comparison_session(self, models: List[str], question: str, files_content: List[Tuple[str, str]] = None) -> Path:
        """Create a comparison session file for multiple models."""
        timestamp = self._get_human_timestamp()
        comparison_file = self.base_dir / f"comparison_{timestamp}.txt"

        content_lines = []
        content_lines.append("=" * 80)
        content_lines.append(f"ASK LLM COMPARISON SESSION")
        content_lines.append("=" * 80)
        content_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append(f"Models: {', '.join(model.upper() for model in models)}")
        content_lines.append("")

        # Add file contents if provided
        if files_content:
            content_lines.append(self._format_file_content(files_content))
            content_lines.append("")

        # Add initial question
        content_lines.append("=" * 40 + " QUESTION " + "=" * 33)
        content_lines.append(question)
        content_lines.append("")

        initial_content = "\n".join(content_lines)
        comparison_file.write_text(initial_content)

        return comparison_file

    def append_comparison_response(self, comparison_file: Path, model_name: str, response: str):
        """Append a model response to comparison file."""
        response_content = []
        response_content.append("=" * 30 + f" {model_name.upper()} RESPONSE " + "=" * (49 - len(model_name)))
        response_content.append(response)
        response_content.append("")

        with open(comparison_file, 'a') as f:
            f.write("\n".join(response_content))

    def list_previous_responses(self, model_name: str, limit: int = 10) -> List[Tuple[str, Path]]:
        """List previous response files for a model."""
        model_dir = self._ensure_model_dir(model_name)

        # Find all timestamped files
        response_files = []
        for file_path in model_dir.glob("*.txt"):
            if file_path.name != "latest_response.txt":
                # Extract timestamp from filename
                timestamp_str = file_path.stem
                try:
                    # Convert timestamp back to readable format
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
                    readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    response_files.append((readable_time, file_path))
                except ValueError:
                    continue

        # Sort by timestamp (newest first) and limit
        response_files.sort(key=lambda x: x[0], reverse=True)
        return response_files[:limit]

    def read_response_file(self, file_path: Path) -> str:
        """Read content of a response file."""
        try:
            return file_path.read_text()
        except Exception as e:
            return f"Error reading file: {e}"

    def extract_context_from_response(self, file_path: Path, include_files: bool = False) -> str:
        """Extract question and response context from a previous session file."""
        try:
            content = file_path.read_text()

            # Extract just the question-response parts, skip file contents if requested
            lines = content.split('\n')
            context_lines = []
            in_question = False
            in_response = False
            skip_files = not include_files

            for line in lines:
                if "=== ATTACHED FILES ===" in line and skip_files:
                    # Skip file content section
                    continue
                elif "===== " in line and "=====" in line and skip_files:
                    # Skip individual file delimiters
                    continue
                elif "QUESTION" in line and "=" in line:
                    in_question = True
                    context_lines.append("Previous Question:")
                elif "RESPONSE" in line and "=" in line:
                    in_question = False
                    in_response = True
                    context_lines.append("Previous Response:")
                elif "FOLLOW-UP" in line and "=" in line:
                    in_question = True
                    context_lines.append("Previous Follow-up:")
                elif in_question or in_response:
                    if line.strip() and not line.startswith("="):
                        context_lines.append(line)

            return "\n".join(context_lines)

        except Exception as e:
            return f"Error extracting context: {e}"

def main():
    """Test the output manager."""
    if len(sys.argv) < 2:
        print("Usage: ask-llm-output-manager.py <test|list> [model_name]")
        sys.exit(1)

    manager = AskLLMOutputManager()

    if sys.argv[1] == "test":
        # Test creating a session
        test_files = [("test.py", "print('hello world')")]
        timestamped, latest = manager.create_session_file("deepseek", "What does this code do?", test_files)
        manager.append_response(timestamped, latest, "This code prints 'hello world' to the console.")
        print(f"Test session created: {timestamped}")

    elif sys.argv[1] == "list" and len(sys.argv) > 2:
        # List previous responses for a model
        model = sys.argv[2]
        responses = manager.list_previous_responses(model)
        print(f"Previous responses for {model}:")
        for timestamp, file_path in responses:
            print(f"  {timestamp}: {file_path.name}")

if __name__ == "__main__":
    main()