"""FFmpeg compositor — combines video segments with audio into final output."""

import subprocess
import tempfile
from pathlib import Path


def overlay_audio(
    video_path: Path,
    audio_path: Path | None,
    output_path: Path,
) -> Path:
    """Overlay an audio track onto a video file.

    If audio_path is None, copies video as-is with a silent audio track.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if audio_path and audio_path.exists():
        # Combine video and audio, using the longer of the two as duration
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                "-movflags", "+faststart",
                str(output_path),
            ],
            capture_output=True,
            check=True,
        )
    else:
        # Add silent audio track
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                "-movflags", "+faststart",
                str(output_path),
            ],
            capture_output=True,
            check=True,
        )

    return output_path


def concatenate_segments(
    segment_files: list[Path],
    output_path: Path,
) -> Path:
    """Concatenate video segments into a single output file using FFmpeg concat demuxer."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg_file in segment_files:
            f.write(f"file '{seg_file.resolve()}'\n")
        concat_list = f.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ],
            capture_output=True,
            check=True,
        )
    finally:
        Path(concat_list).unlink(missing_ok=True)

    return output_path


def compose_walkthrough(
    video_segments: list[Path],
    audio_segments: list[Path | None],
    output_path: Path,
) -> Path:
    """Full pipeline: overlay audio on each segment, then concatenate.

    Args:
        video_segments: List of rendered video segment files.
        audio_segments: List of audio files (None for segments without audio).
        output_path: Final output video path.

    Returns:
        Path to the final composed video.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        combined = []

        for i, (video, audio) in enumerate(zip(video_segments, audio_segments)):
            out = tmpdir / f"combined_{i:02d}.mp4"
            print(f"  Compositing segment {i}...")
            overlay_audio(video, audio, out)
            combined.append(out)

        print(f"  Concatenating {len(combined)} segments...")
        return concatenate_segments(combined, output_path)
