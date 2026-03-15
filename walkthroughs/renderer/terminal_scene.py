"""Manim scene for terminal/SQL output with typewriter effect."""

from manim import *

from . import theme


class TerminalScene(Scene):
    """Renders terminal output with a typewriter animation."""

    def __init__(
        self,
        content: str,
        duration: float = 8.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content.strip()
        self.segment_duration = duration

    def construct(self):
        self.camera.background_color = theme.BG_COLOR

        # Terminal background
        terminal_bg = RoundedRectangle(
            width=theme.CODE_AREA_WIDTH + 0.4,
            height=theme.CODE_AREA_HEIGHT + 0.2,
            corner_radius=0.15,
            fill_color=theme.TERMINAL_BG,
            fill_opacity=1,
            stroke_color="#444444",
            stroke_width=1,
        )

        # Terminal title bar
        title_bar = Rectangle(
            width=terminal_bg.width,
            height=0.35,
            fill_color="#333333",
            fill_opacity=1,
            stroke_width=0,
        )
        title_bar.next_to(terminal_bg, UP, buff=0)

        # Window buttons
        buttons = VGroup()
        for color in ["#ff5f56", "#ffbd2e", "#27c93f"]:
            btn = Dot(radius=0.06, color=color, fill_opacity=1)
            buttons.add(btn)
        buttons.arrange(RIGHT, buff=0.12)
        buttons.move_to(title_bar).align_to(title_bar, LEFT).shift(RIGHT * 0.3)

        terminal_group = VGroup(terminal_bg, title_bar, buttons)
        terminal_group.center()

        self.play(FadeIn(terminal_group), run_time=0.5)

        # Split content into lines and render with typewriter effect
        lines = self.content.split("\n")
        text_objects = []

        # Calculate how much space we have
        available_height = theme.CODE_AREA_HEIGHT - 0.4
        max_lines = int(available_height / 0.35)
        display_lines = lines[:max_lines]

        # Create all text objects positioned
        start_y = terminal_bg.get_top()[1] - 0.5
        for i, line in enumerate(display_lines):
            if not line.strip():
                continue
            text = Text(
                line,
                font="Monospace",
                font_size=theme.TERMINAL_FONT_SIZE,
                color=theme.TEXT_COLOR,
            )
            if text.width > theme.CODE_AREA_WIDTH - 0.4:
                text.scale_to_fit_width(theme.CODE_AREA_WIDTH - 0.4)
            text.move_to(
                terminal_bg.get_left() + RIGHT * (0.3 + text.width / 2)
            )
            text.set_y(start_y - i * 0.35)
            text_objects.append(text)

        # Type out lines
        type_time = min(self.segment_duration * 0.5, len(text_objects) * 0.4)
        per_line = type_time / max(len(text_objects), 1)

        for text in text_objects:
            self.play(FadeIn(text, shift=RIGHT * 0.1), run_time=per_line)

        # Hold
        elapsed = 0.5 + type_time + 0.5
        remaining = max(0.5, self.segment_duration - elapsed)
        self.wait(remaining)

        # Fade out
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
