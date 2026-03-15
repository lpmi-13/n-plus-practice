"""Manim scene for before/after code diff animation."""

from manim import *

from . import theme


class DiffScene(Scene):
    """Shows a before/after code comparison with animated transition."""

    def __init__(
        self,
        file_path: str,
        before: str,
        after: str,
        duration: float = 10.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.before = before.strip()
        self.after = after.strip()
        self.segment_duration = duration

    def construct(self):
        self.camera.background_color = theme.BG_COLOR

        # File label
        file_label = Text(
            self.file_path,
            font_size=16,
            color=theme.SUBTITLE_COLOR,
        )

        # "Before" label and code
        before_label = Text(
            "BEFORE",
            font_size=20,
            color="#f85149",
            weight=BOLD,
        )

        before_code = Code(
            code_string=self.before,
            language="python",
            tab_width=4,
            formatter_style="monokai",
            background="rectangle",
            background_config={
                "stroke_color": "#f85149",
                "stroke_width": 1,
            },
            paragraph_config={
                "font_size": theme.CODE_FONT_SIZE - 2,
            },
        )
        if before_code.width > theme.CODE_AREA_WIDTH:
            before_code.scale_to_fit_width(theme.CODE_AREA_WIDTH)

        # "After" label and code
        after_label = Text(
            "AFTER",
            font_size=20,
            color="#3fb950",
            weight=BOLD,
        )

        after_code = Code(
            code_string=self.after,
            language="python",
            tab_width=4,
            formatter_style="monokai",
            background="rectangle",
            background_config={
                "stroke_color": "#3fb950",
                "stroke_width": 1,
            },
            paragraph_config={
                "font_size": theme.CODE_FONT_SIZE - 2,
            },
        )
        if after_code.width > theme.CODE_AREA_WIDTH:
            after_code.scale_to_fit_width(theme.CODE_AREA_WIDTH)

        # Position before group
        file_label.to_edge(UP, buff=0.3)
        before_label.next_to(file_label, DOWN, buff=0.3).align_to(
            file_label, LEFT
        )
        before_code.next_to(before_label, DOWN, buff=0.2)
        before_code.center().shift(DOWN * 0.3)

        # Show before
        self.play(
            FadeIn(file_label),
            FadeIn(before_label),
            FadeIn(before_code),
            run_time=0.8,
        )

        # Red highlight overlay on before code
        before_highlight = SurroundingRectangle(
            before_code,
            color="#f85149",
            fill_color="#f8514920",
            fill_opacity=0.15,
            buff=0.1,
            stroke_width=1,
        )
        self.play(FadeIn(before_highlight), run_time=0.3)
        self.wait(self.segment_duration * 0.25)

        # Transition: before slides left/fades, after appears
        after_label.next_to(file_label, DOWN, buff=0.3).align_to(
            file_label, LEFT
        )
        after_code.next_to(after_label, DOWN, buff=0.2)
        after_code.center().shift(DOWN * 0.3)

        after_highlight = SurroundingRectangle(
            after_code,
            color="#3fb950",
            fill_color="#3fb95020",
            fill_opacity=0.15,
            buff=0.1,
            stroke_width=1,
        )

        self.play(
            FadeOut(before_code, shift=LEFT),
            FadeOut(before_label, shift=LEFT),
            FadeOut(before_highlight),
            run_time=0.6,
        )
        self.play(
            FadeIn(after_label, shift=RIGHT * 0.2),
            FadeIn(after_code, shift=RIGHT * 0.2),
            run_time=0.6,
        )
        self.play(FadeIn(after_highlight), run_time=0.3)

        # Hold
        elapsed = 0.8 + 0.3 + self.segment_duration * 0.25 + 0.6 + 0.6 + 0.3 + 0.5
        remaining = max(0.5, self.segment_duration - elapsed)
        self.wait(remaining)

        # Fade out
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
