"""Calculate audio durations for timing synchronization."""

import subprocess
from pathlib import Path


def get_audio_duration(audio_path: str | Path) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 5.0  # fallback default


def calculate_durations(
    audio_files: list[Path | None],
    min_duration: float = 3.0,
    padding: float = 1.5,
) -> list[float]:
    """Calculate video segment durations from audio files.

    Each segment's video duration = audio duration + padding,
    with a minimum duration for segments without audio.

    Args:
        audio_files: List of audio file paths (None for segments without audio).
        min_duration: Minimum duration for any segment.
        padding: Extra time added after audio to let visuals breathe.

    Returns:
        List of durations in seconds.
    """
    durations = []
    for audio_path in audio_files:
        if audio_path and audio_path.exists():
            audio_dur = get_audio_duration(audio_path)
            durations.append(max(min_duration, audio_dur + padding))
        else:
            durations.append(min_duration)
    return durations
