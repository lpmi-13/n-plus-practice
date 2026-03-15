"""TTS narration generator using edge-tts."""

import asyncio
from pathlib import Path

import edge_tts

# Good voices for technical narration
DEFAULT_VOICE = "en-US-GuyNeural"
FALLBACK_VOICE = "en-US-AriaNeural"


async def _generate_audio(text: str, output_path: Path, voice: str) -> Path:
    """Generate a single audio file from text using edge-tts."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


def generate_narration(
    segments: list,
    output_dir: str | Path,
    voice: str = DEFAULT_VOICE,
) -> list[Path]:
    """Generate audio files for all segments in a walkthrough spec.

    Args:
        segments: List of Segment objects from the spec.
        output_dir: Directory to write audio files.
        voice: edge-tts voice name.

    Returns:
        List of paths to generated .mp3 audio files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_files = []

    for i, segment in enumerate(segments):
        narration = segment.narration.strip()
        if not narration:
            audio_files.append(None)
            continue

        out_file = output_dir / f"segment_{i:02d}.mp3"
        print(f"  Generating audio for segment {i}: {segment.type}...")

        try:
            asyncio.run(_generate_audio(narration, out_file, voice))
        except Exception as e:
            print(f"    Warning: TTS failed with {voice}, trying fallback: {e}")
            try:
                asyncio.run(_generate_audio(narration, out_file, FALLBACK_VOICE))
            except Exception as e2:
                print(f"    Error: TTS fallback also failed: {e2}")
                audio_files.append(None)
                continue

        audio_files.append(out_file)

    return audio_files
