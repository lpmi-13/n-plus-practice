"""TTS narration generator with pluggable backends (edge-tts, Kokoro).

Applies pronunciation preprocessing to all narration text before synthesis.
"""

import asyncio
from pathlib import Path
from typing import Literal

from walkthroughs.narrator.pronunciation import preprocess_narration

# ── Backend: edge-tts ──────────────────────────────────────────────

EDGE_DEFAULT_VOICE = "en-US-GuyNeural"
EDGE_FALLBACK_VOICE = "en-US-AriaNeural"


async def _generate_edge(text: str, output_path: Path, voice: str) -> Path:
    """Generate audio using edge-tts (Microsoft Edge, no API key)."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


# ── Backend: Kokoro ────────────────────────────────────────────────

# Default voice pack shipped with kokoro.  Override via generate_narration().
KOKORO_DEFAULT_VOICE = "af_heart"


def _generate_kokoro(
    text: str,
    output_path: Path,
    voice: str,
    speed: float = 1.0,
) -> Path:
    """Generate audio using Kokoro (local, CPU-friendly, Apache 2.0).

    Requires:
        uv sync --extra video --extra kokoro
        # or
        pip install -r requirements-video.txt "kokoro>=0.8" numpy
    """
    try:
        from kokoro import KPipeline
    except ImportError as exc:
        raise RuntimeError(
            "Kokoro is not installed.  Install with:\n"
            "  uv sync --extra video --extra kokoro\n"
            "  # or\n"
            '  pip install -r requirements-video.txt "kokoro>=0.8" numpy\n'
            "Or use --tts-backend edge (the default)."
        ) from exc

    import soundfile as sf

    pipeline = KPipeline(lang_code="a")
    # Generate returns an iterator of (graphemes, phonemes, audio) tuples.
    # Concatenate all audio chunks for the full utterance.
    audio_chunks = []
    for _gs, _ps, audio in pipeline(text, voice=voice, speed=speed):
        if audio is not None:
            audio_chunks.append(audio)

    if not audio_chunks:
        raise RuntimeError(f"Kokoro produced no audio for: {text[:80]!r}")

    import numpy as np

    full_audio = np.concatenate(audio_chunks)

    # Kokoro outputs 24 kHz audio
    sf.write(str(output_path), full_audio, 24000)
    return output_path


# ── Public API ─────────────────────────────────────────────────────

TTS_BACKENDS = ("edge", "kokoro")
TTSBackend = Literal["edge", "kokoro"]


def generate_narration(
    segments: list,
    output_dir: str | Path,
    *,
    backend: TTSBackend = "edge",
    voice: str | None = None,
    speed: float = 1.0,
    preprocess: bool = True,
) -> list[Path | None]:
    """Generate audio files for all segments in a walkthrough spec.

    Args:
        segments: List of Segment objects from the spec.
        output_dir: Directory to write audio files.
        backend: TTS backend to use ("edge" or "kokoro").
        voice: Voice name/ID.  Defaults depend on backend.
        speed: Speaking speed multiplier (Kokoro only).
        preprocess: Whether to apply pronunciation preprocessing.

    Returns:
        List of paths to generated audio files (None for silent segments).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve default voice per backend
    if voice is None:
        voice = (
            EDGE_DEFAULT_VOICE if backend == "edge" else KOKORO_DEFAULT_VOICE
        )

    ext = ".mp3" if backend == "edge" else ".wav"
    audio_files: list[Path | None] = []

    for i, segment in enumerate(segments):
        narration = segment.narration.strip()
        if not narration:
            audio_files.append(None)
            continue

        # Apply pronunciation preprocessing
        if preprocess:
            narration = preprocess_narration(narration)

        out_file = output_dir / f"segment_{i:02d}{ext}"
        print(f"  [{backend}] Generating audio for segment {i}: {segment.type}...")

        try:
            if backend == "kokoro":
                _generate_kokoro(narration, out_file, voice, speed=speed)
            else:
                try:
                    asyncio.run(_generate_edge(narration, out_file, voice))
                except Exception as e:
                    print(f"    Warning: edge-tts failed with {voice}, trying fallback: {e}")
                    asyncio.run(
                        _generate_edge(narration, out_file, EDGE_FALLBACK_VOICE)
                    )
        except Exception as exc:
            print(f"    Error: TTS generation failed: {exc}")
            audio_files.append(None)
            continue

        audio_files.append(out_file)

    return audio_files
