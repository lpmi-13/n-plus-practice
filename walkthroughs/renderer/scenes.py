"""Orchestrator that renders a walkthrough spec into video segments."""

import tempfile
from pathlib import Path

from manim import *

from . import theme
from .code_display import CodeDisplayScene
from .diff_scene import DiffScene
from .terminal_scene import TerminalScene


class IntroScene(Scene):
    """Title card scene for intro/outro segments."""

    def __init__(self, title: str, is_outro: bool = False, duration: float = 5.0, **kwargs):
        super().__init__(**kwargs)
        self.title_text = title
        self.is_outro = is_outro
        self.segment_duration = duration

    def construct(self):
        self.camera.background_color = theme.BG_COLOR

        # Accent line
        line = Line(LEFT * 3, RIGHT * 3, color=theme.ACCENT_COLOR, stroke_width=3)

        title = Text(
            self.title_text,
            font_size=theme.TITLE_FONT_SIZE,
            color=theme.TITLE_COLOR,
            weight=BOLD,
        )
        if title.width > theme.FRAME_WIDTH - 2:
            title.scale_to_fit_width(theme.FRAME_WIDTH - 2)

        subtitle_text = (
            "N+1 Query Practice"
            if not self.is_outro
            else "Ready to practice? Check the exercises/ folder."
        )
        subtitle = Text(
            subtitle_text,
            font_size=theme.SUBTITLE_FONT_SIZE,
            color=theme.SUBTITLE_COLOR,
        )

        group = VGroup(title, line, subtitle).arrange(DOWN, buff=0.4)
        group.center()

        self.play(
            FadeIn(title, shift=DOWN * 0.3),
            GrowFromCenter(line),
            run_time=1.0,
        )
        self.play(FadeIn(subtitle, shift=UP * 0.2), run_time=0.5)

        remaining = max(0.5, self.segment_duration - 2.0)
        self.wait(remaining)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)


def _build_scene(segment, duration: float):
    """Create a Manim Scene instance from a spec segment."""
    seg_type = segment.type

    if seg_type in ("intro", "outro"):
        return IntroScene(
            title=segment.title or segment.narration[:50],
            is_outro=(seg_type == "outro"),
            duration=duration,
        )
    elif seg_type == "code_display":
        return CodeDisplayScene(
            file_path=segment.file,
            lines=segment.lines,
            highlight_lines=segment.highlight_lines,
            annotation=segment.annotation,
            duration=duration,
        )
    elif seg_type == "terminal_output":
        return TerminalScene(
            content=segment.content,
            duration=duration,
        )
    elif seg_type == "code_diff":
        return DiffScene(
            file_path=segment.file or "",
            before=segment.before or "",
            after=segment.after or "",
            duration=duration,
        )
    else:
        raise ValueError(f"Unknown segment type: {seg_type}")


def render_segment(
    segment,
    output_path: str | Path,
    duration: float = 8.0,
    quality: str = "low",
) -> Path:
    """Render a single segment to a video file.

    Args:
        segment: A Segment from the walkthrough spec.
        output_path: Where to write the output video.
        duration: How long the segment should last.
        quality: Manim quality flag — "low", "medium", or "high".

    Returns:
        Path to the rendered video file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    quality_map = {
        "low": "-ql",
        "medium": "-qm",
        "high": "-qh",
    }
    q_flag = quality_map.get(quality, "-ql")

    import shutil

    scene = _build_scene(segment, duration)

    # Let manim use its default media directory
    # We'll find and move the output file after rendering
    config.output_file = output_path.stem

    if quality == "low":
        config.pixel_height = 480
        config.pixel_width = 854
        config.frame_rate = 15
    elif quality == "medium":
        config.pixel_height = 720
        config.pixel_width = 1280
        config.frame_rate = 30
    else:
        config.pixel_height = 1080
        config.pixel_width = 1920
        config.frame_rate = 30

    config.disable_caching = True

    # Record which mp4 files exist before rendering
    media_dir = Path.cwd() / "media"
    existing_files = set()
    if media_dir.exists():
        existing_files = set(media_dir.rglob("*.mp4"))

    scene.render()

    # Find newly created mp4 files
    if media_dir.exists():
        all_files = set(media_dir.rglob("*.mp4"))
        new_files = all_files - existing_files
        if new_files:
            # Pick the newest
            newest = max(new_files, key=lambda p: p.stat().st_mtime)
            shutil.move(str(newest), str(output_path))
            return output_path

    # Fallback: look for any mp4 matching the scene name
    video_files = list(media_dir.rglob("*.mp4")) if media_dir.exists() else []
    if video_files:
        video_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        shutil.move(str(video_files[0]), str(output_path))
        return output_path

    raise RuntimeError(f"No video file produced for segment: {segment.type}")


def render_spec(
    spec_path: str | Path,
    output_dir: str | Path | None = None,
    quality: str = "low",
    audio: bool = False,
    durations: list[float] | None = None,
) -> list[Path]:
    """Render all segments from a walkthrough spec.

    Args:
        spec_path: Path to the YAML spec file.
        output_dir: Directory for output files. Defaults to walkthroughs/output/.
        quality: Manim quality — "low", "medium", or "high".
        audio: If False, renders silent video only.
        durations: Per-segment durations (from TTS timing). If None, uses defaults.

    Returns:
        List of paths to rendered segment video files.
    """
    from walkthroughs.renderer import load_spec

    spec = load_spec(spec_path)

    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / "output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    segment_dir = output_dir / f"{spec.exercise}_segments"
    segment_dir.mkdir(parents=True, exist_ok=True)

    rendered_files = []
    for i, segment in enumerate(spec.segments):
        if durations and i < len(durations):
            duration = durations[i]
        else:
            # Default durations by type
            default_durations = {
                "intro": 5.0,
                "outro": 5.0,
                "code_display": 8.0,
                "terminal_output": 8.0,
                "code_diff": 10.0,
            }
            duration = default_durations.get(segment.type, 8.0)

        out_file = segment_dir / f"segment_{i:02d}_{segment.type}.mp4"
        print(f"  Rendering segment {i}: {segment.type}...")
        render_segment(segment, out_file, duration=duration, quality=quality)
        rendered_files.append(out_file)

    return rendered_files
