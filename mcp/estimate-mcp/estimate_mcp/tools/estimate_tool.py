"""
EstimateTool - Analyzes filesystem timestamps to provide fact-based completion estimates.
"""

import os
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field

from .base_tool import BaseTool

class EstimateInput(BaseModel):
    """Input schema for EstimateTool."""
    pattern: str = Field(..., description="Glob pattern for completed files (e.g., 'data/*/DONE')")
    total: int = Field(..., description="Total expected number of completions")
    base_dir: Optional[str] = Field(default=None, description="Base directory to search from (default: current dir)")

class EstimateOutput(BaseModel):
    """Output schema for EstimateTool."""
    pattern: str
    completed: int
    total: int
    remaining: int
    percent_complete: float

    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None

    elapsed_seconds: Optional[float] = None
    elapsed_hours: Optional[float] = None
    elapsed_days: Optional[float] = None

    avg_seconds_per_file: Optional[float] = None
    avg_minutes_per_file: Optional[float] = None
    files_per_hour: Optional[float] = None

    recent_files_per_hour: Optional[float] = None

    hours_remaining: Optional[float] = None
    days_remaining: Optional[float] = None
    eta_timestamp: Optional[str] = None
    eta_human: Optional[str] = None

    error: Optional[str] = None

class EstimateTool(BaseTool[EstimateInput, EstimateOutput]):
    """
    Tool for analyzing filesystem timestamps to provide fact-based completion estimates.

    NO GUESSING. ONLY MEASURED RATES FROM ACTUAL FILESYSTEM TIMESTAMPS.
    """

    input_schema = EstimateInput
    output_schema = EstimateOutput

    def _run(self, input_obj: EstimateInput) -> EstimateOutput:
        """
        Analyze actual file timestamps to calculate completion rate and ETA.

        Args:
            input_obj: An instance of EstimateInput.

        Returns:
            An instance of EstimateOutput with measured statistics.
        """
        pattern = input_obj.pattern
        total_expected = input_obj.total
        base_dir = input_obj.base_dir

        if base_dir:
            pattern = str(Path(base_dir) / pattern)

        try:
            files = glob.glob(pattern, recursive=True)
        except Exception as e:
            return EstimateOutput(
                pattern=pattern,
                completed=0,
                total=total_expected,
                remaining=total_expected,
                percent_complete=0.0,
                error=f"Error globbing pattern: {str(e)}"
            )

        if not files:
            return EstimateOutput(
                pattern=pattern,
                completed=0,
                total=total_expected,
                remaining=total_expected,
                percent_complete=0.0,
                error=f"No files found matching pattern: {pattern}"
            )

        # Get timestamps
        timestamps = []
        for f in files:
            try:
                stat = os.stat(f)
                timestamps.append({
                    'file': f,
                    'timestamp': stat.st_mtime
                })
            except OSError:
                continue

        if not timestamps:
            return EstimateOutput(
                pattern=pattern,
                completed=0,
                total=total_expected,
                remaining=total_expected,
                percent_complete=0.0,
                error="Could not read timestamps from files"
            )

        # Sort chronologically
        timestamps.sort(key=lambda x: x['timestamp'])

        completed = len(timestamps)
        remaining = total_expected - completed

        # Measured time span
        first_ts = timestamps[0]['timestamp']
        last_ts = timestamps[-1]['timestamp']

        elapsed_seconds = last_ts - first_ts
        elapsed_hours = elapsed_seconds / 3600

        # Measured rate (actual, not guessed)
        if elapsed_seconds > 0 and completed > 1:
            files_per_hour = (completed - 1) / elapsed_hours
            avg_seconds_per_file = elapsed_seconds / (completed - 1)
            avg_minutes_per_file = avg_seconds_per_file / 60
        else:
            files_per_hour = None
            avg_seconds_per_file = None
            avg_minutes_per_file = None

        # ETA based on measured rate
        if files_per_hour and files_per_hour > 0:
            hours_remaining = remaining / files_per_hour
            days_remaining = hours_remaining / 24
            eta_datetime = datetime.fromtimestamp(last_ts) + timedelta(hours=hours_remaining)
        else:
            hours_remaining = None
            days_remaining = None
            eta_datetime = None

        # Recent rate (last 10 files)
        if len(timestamps) >= 10:
            recent_first = timestamps[-10]['timestamp']
            recent_last = timestamps[-1]['timestamp']
            recent_elapsed = recent_last - recent_first
            recent_rate = 9 / (recent_elapsed / 3600) if recent_elapsed > 0 else None
        else:
            recent_rate = None

        return EstimateOutput(
            pattern=pattern,
            completed=completed,
            total=total_expected,
            remaining=remaining,
            percent_complete=(completed / total_expected) * 100,

            first_timestamp=datetime.fromtimestamp(first_ts).isoformat(),
            last_timestamp=datetime.fromtimestamp(last_ts).isoformat(),

            elapsed_seconds=round(elapsed_seconds, 2) if elapsed_seconds else None,
            elapsed_hours=round(elapsed_hours, 2) if elapsed_hours else None,
            elapsed_days=round(elapsed_hours / 24, 2) if elapsed_hours else None,

            avg_seconds_per_file=round(avg_seconds_per_file, 2) if avg_seconds_per_file else None,
            avg_minutes_per_file=round(avg_minutes_per_file, 2) if avg_minutes_per_file else None,
            files_per_hour=round(files_per_hour, 2) if files_per_hour else None,

            recent_files_per_hour=round(recent_rate, 2) if recent_rate else None,

            hours_remaining=round(hours_remaining, 2) if hours_remaining else None,
            days_remaining=round(days_remaining, 2) if days_remaining else None,
            eta_timestamp=eta_datetime.isoformat() if eta_datetime else None,
            eta_human=eta_datetime.strftime('%Y-%m-%d %H:%M') if eta_datetime else None
        )
