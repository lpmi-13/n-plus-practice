"""Manim scene for displaying syntax-highlighted code with annotations."""

from pathlib import Path

from manim import *

from . import theme


class CodeDisplayScene(Scene):
    """Renders a code file with syntax highlighting and optional line highlights."""

    def __init__(
        self,
        file_path: str,
        lines: list[int] | None = None,
        highlight_lines: list[int] | None = None,
        annotation: str | None = None,
        duration: float = 8.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.lines = lines  # [start, end] range to show
        self.highlight_lines = highlight_lines or []
        self.annotation = annotation
        self.segment_duration = duration

    def construct(self):
        self.camera.background_color = theme.BG_COLOR

        # Read file content
        repo_root = Path(__file__).resolve().parent.parent.parent
        full_path = repo_root / self.file_path
        with open(full_path) as f:
            all_lines = f.readlines()

        # Extract line range
        if self.lines and len(self.lines) == 2:
            start, end = self.lines[0] - 1, self.lines[1]
            code_lines = all_lines[start:end]
            line_offset = self.lines[0]
        else:
            code_lines = all_lines
            line_offset = 1

        code_text = "".join(code_lines)

        # Create code block using manim's Code mobject
        code = Code(
            code_string=code_text,
            language="python",
            tab_width=4,
            formatter_style="monokai",
            background="rectangle",
            line_numbers_from=line_offset,
            background_config={
                "stroke_color": theme.ACCENT_COLOR,
                "stroke_width": 1,
            },
            paragraph_config={
                "font_size": theme.CODE_FONT_SIZE,
            },
        )
        if code.width > theme.CODE_AREA_WIDTH:
            code.scale_to_fit_width(theme.CODE_AREA_WIDTH)
        if code.height > theme.CODE_AREA_HEIGHT:
            code.scale_to_fit_height(theme.CODE_AREA_HEIGHT)

        if self.annotation:
            code.shift(UP * 0.5)
        else:
            code.center()

        # File path label
        file_label = Text(
            self.file_path,
            font_size=16,
            color=theme.SUBTITLE_COLOR,
        )
        file_label.next_to(code, UP, buff=0.2).align_to(code, LEFT)

        # Animate code appearing
        self.play(FadeIn(file_label), FadeIn(code), run_time=0.8)

        # Highlight specific lines
        if self.highlight_lines and hasattr(code, "code"):
            highlights = VGroup()
            for line_no in self.highlight_lines:
                idx = line_no - line_offset
                if 0 <= idx < len(code.code.chars):
                    line_mob = code.code.chars[idx]
                    hl_rect = SurroundingRectangle(
                        line_mob,
                        color=theme.HIGHLIGHT_COLOR,
                        fill_color=theme.HIGHLIGHT_COLOR,
                        fill_opacity=0.3,
                        buff=0.05,
                        stroke_width=0,
                    )
                    highlights.add(hl_rect)

            if highlights:
                self.play(FadeIn(highlights), run_time=0.5)

        # Annotation
        if self.annotation:
            ann_text = Text(
                self.annotation,
                font_size=theme.ANNOTATION_FONT_SIZE,
                color=theme.ANNOTATION_COLOR,
            )
            ann_text.next_to(code, DOWN, buff=0.4)
            if ann_text.width > theme.CODE_AREA_WIDTH:
                ann_text.scale_to_fit_width(theme.CODE_AREA_WIDTH)
            self.play(FadeIn(ann_text, shift=UP * 0.2), run_time=0.5)

        # Hold for remaining duration
        elapsed = 1.8 if self.annotation else 1.3
        if self.highlight_lines:
            elapsed += 0.5
        remaining = max(0.5, self.segment_duration - elapsed - 0.5)
        self.wait(remaining)

        # Fade out
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
