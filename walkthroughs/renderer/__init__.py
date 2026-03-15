"""Walkthrough spec parser and Manim renderer."""

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel


class Segment(BaseModel):
    type: Literal[
        "intro", "code_display", "terminal_output", "code_diff", "outro"
    ]
    narration: str
    # intro/outro fields
    visual: Optional[str] = None
    title: Optional[str] = None
    # code_display fields
    file: Optional[str] = None
    lines: Optional[list[int]] = None
    highlight_lines: Optional[list[int]] = None
    annotation: Optional[str] = None
    # terminal_output fields
    content: Optional[str] = None
    # code_diff fields
    before: Optional[str] = None
    after: Optional[str] = None


class WalkthroughSpec(BaseModel):
    exercise: str
    title: str
    duration_target: str
    segments: list[Segment]


def load_spec(path: str | Path) -> WalkthroughSpec:
    """Load and validate a walkthrough spec from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return WalkthroughSpec(**data)
