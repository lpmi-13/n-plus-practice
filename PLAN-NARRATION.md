# N+1 Query Practice Environment â€” Phase 2: Video & Narration Pipeline

## Repository

https://github.com/lpmi-13/n-plus-practice

## Context

Phase 1 (MVP) is complete. The repo has a working Django + Strawberry GraphQL practice environment with deliberate N+1 problems, three progressive exercises, a query-counting validation harness, and Docker Compose orchestration. See the existing `PLAN.md` for the MVP architecture.

Phase 2 adds a **video walkthrough pipeline** that programmatically generates animated code walkthroughs with narration for each exercise. The goal: a learner can watch a worked example video before tackling the parallel practice exercise themselves.

---

## Architecture Decisions

### Design Principles

The original architectural discussion identified three phases: **author** (generate example), **present** (video + narration), and **practice** (learner environment). Phase 1 covered author + practice. Phase 2 covers **present** â€” taking the existing exercise content and producing video walkthroughs from it.

Key insight from the original design: the **scenario definition is the single source of truth**. The video pipeline should derive everything from structured metadata, not from ad-hoc scripts. This means we define a walkthrough specification format, and the rendering + narration layers consume it.

### Stack Additions

- **Manim Community Edition** â€” programmatic animation engine (Python). Produces animated code displays, syntax highlighting, annotation overlays, and visual transitions. Much better fit than screen recording for reproducible, editable walkthroughs.
- **Kokoro TTS** (82M params, Apache 2.0) â€” lightweight open-source text-to-speech. Runs on CPU, no API keys needed, good quality for narration. Fallback option: `edge-tts` (Microsoft Edge TTS, free, async, no GPU).
- **FFmpeg** â€” compositing video + audio into final output. Already available in the Docker image.
- **Pygments** â€” syntax highlighting for code snippets rendered in Manim scenes.

### Why Manim over Screen Recording

Screen recording is fragile (resolution-dependent, OS-dependent, hard to version control). Manim generates videos from Python code, which means:
- Walkthroughs are deterministic and reproducible
- They can be regenerated when code changes
- Timing, pacing, and annotations are precise
- Everything lives in version control
- No manual editing needed

### Walkthrough Specification Format

Each exercise gets a `walkthrough.yaml` file that defines the video content:

```yaml
exercise: "01_basic"
title: "Fixing N+1 Queries with select_related"
duration_target: "3-5 minutes"

segments:
  - type: "intro"
    narration: "In this walkthrough, we'll fix an N+1 query in our product listing. Let's start by looking at the problem."
    visual: "title_card"

  - type: "code_display"
    file: "catalog/schema.py"
    highlight_lines: [15, 16, 17]
    narration: "Here's our ProductType resolver. Notice it accesses self.category directly â€” this triggers a lazy load for every single product."
    annotation: "This triggers a separate SQL query for each product!"

  - type: "terminal_output"
    content: "SELECT * FROM catalog_product; SELECT * FROM catalog_category WHERE id = 1; SELECT * FROM catalog_category WHERE id = 2; ..."
    narration: "When we run our GraphQL query, look at the SQL output â€” 31 queries for 30 products, each fetching its category one at a time."

  - type: "code_diff"
    file: "catalog/schema.py"
    before_lines: [15, 16, 17]
    after_lines: [15, 16, 17, 18]
    narration: "The fix is simple â€” we add select_related to our queryset. This tells Django to JOIN the category table in a single query."

  - type: "terminal_output"
    content: "SELECT catalog_product.*, catalog_category.* FROM catalog_product INNER JOIN catalog_category ON ..."
    narration: "Now we're down to just one query. Django fetches everything in a single JOIN."

  - type: "validation"
    command: "make check q=products_with_category"
    narration: "Let's verify with our test harness â€” query count dropped from 31 to 1. Exercise complete."

  - type: "outro"
    narration: "That's select_related â€” use it whenever you're traversing a ForeignKey. In the next exercise, we'll tackle reverse relations with prefetch_related."
    visual: "title_card"
```

This format is the **single source of truth** for each walkthrough. The Manim renderer and TTS engine both consume it.

### Project Layout Additions

```
repo-root/
â”œâ”€â”€ ... (existing MVP files)
â”œâ”€â”€ walkthroughs/                    # NEW â€” video pipeline
â”‚   â”œâ”€â”€ specs/                       # Walkthrough specifications
â”‚   â”‚   â”œâ”€â”€ 01_basic.yaml
â”‚   â”‚   â”œâ”€â”€ 02_intermediate.yaml
â”‚   â”‚   â””â”€â”€ 03_advanced.yaml
â”‚   â”œâ”€â”€ renderer/                    # Manim scene generators
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ scenes.py                # Manim Scene classes for each segment type
â”‚   â”‚   â”œâ”€â”€ code_display.py          # Animated code display with highlighting
â”‚   â”‚   â”œâ”€â”€ terminal_scene.py        # Terminal/SQL output animation
â”‚   â”‚   â”œâ”€â”€ diff_scene.py            # Before/after code diff animation
â”‚   â”‚   â””â”€â”€ theme.py                 # Colors, fonts, layout constants
â”‚   â”œâ”€â”€ narrator/                    # TTS narration generator
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ generate.py              # Reads spec, produces audio segments
â”‚   â”‚   â””â”€â”€ timing.py                # Calculates segment durations from audio
â”‚   â”œâ”€â”€ compositor/                  # Combines video + audio
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ compose.py               # FFmpeg wrapper for final assembly
â”‚   â”œâ”€â”€ cli.py                       # CLI entry point: generate one or all walkthroughs
â”‚   â””â”€â”€ output/                      # Generated videos (gitignored)
â”‚       â”œâ”€â”€ 01_basic.mp4
â”‚       â”œâ”€â”€ 02_intermediate.mp4
â”‚       â””â”€â”€ 03_advanced.mp4
â”œâ”€â”€ requirements-video.txt           # Additional deps for the video pipeline
â””â”€â”€ Makefile                         # Updated with video generation targets
```

---

## PR Breakdown

### PR 7: Video Pipeline Skeleton & Walkthrough Spec Format

**Branch:** `07-video-pipeline-skeleton`

**Scope:**
- `walkthroughs/` directory structure as shown above
- `walkthroughs/specs/01_basic.yaml` â€” complete walkthrough spec for exercise 01
- `walkthroughs/specs/02_intermediate.yaml` â€” stub with intro/outro only (filled in PR 10)
- `walkthroughs/specs/03_advanced.yaml` â€” stub with intro/outro only (filled in PR 10)
- A Python dataclass or Pydantic model in `walkthroughs/renderer/__init__.py` that parses and validates the YAML spec format
- `requirements-video.txt` with manim, pyyaml, pydantic
- `walkthroughs/cli.py` â€” skeleton CLI using argparse, with `generate`, `validate`, and `list` subcommands. `validate` parses a spec and reports errors; `list` shows available specs; `generate` is a stub that prints "not yet implemented"
- Update `.gitignore` to ignore `walkthroughs/output/`
- Update `README.md` with a brief section on the video pipeline

**Acceptance criteria:**
- `python -m walkthroughs.cli validate --spec walkthroughs/specs/01_basic.yaml` passes
- `python -m walkthroughs.cli list` shows all three specs
- The spec model catches malformed YAML (missing required fields, invalid segment types)

**Claude Code prompt:**
```
Read PLAN-phase2.md in the repo root. Implement PR 7: Video Pipeline Skeleton
& Walkthrough Spec Format. Create branch 07-video-pipeline-skeleton from main.
Follow the architecture and project layout exactly. The walkthrough spec for
exercise 01 should fully cover the select_related fix, referencing the actual
code in catalog/schema.py. Use conventional commits, push, and open a PR.
```

---

### PR 8: Manim Renderer â€” Code Display & Diff Scenes

**Branch:** `08-manim-renderer`
**Base:** `main` (after PR 7 merged)

**Scope:**
- `walkthroughs/renderer/theme.py` â€” color palette (dark theme with syntax colors matching VS Code Dark+), font choices (monospace for code, sans-serif for annotations), layout grid constants (code area, annotation area, padding)
- `walkthroughs/renderer/code_display.py` â€” Manim Scene that:
  - Renders a code file with Pygments syntax highlighting
  - Animates line-by-line appearance or highlights specific lines
  - Supports annotation text that appears alongside highlighted code
  - Scrolls through long files smoothly
- `walkthroughs/renderer/terminal_scene.py` â€” Manim Scene that:
  - Renders a terminal/console aesthetic (dark background, monospace, prompt chars)
  - Types out SQL queries line by line with a typewriter effect
  - Supports highlighting specific queries in red/green for before/after
- `walkthroughs/renderer/diff_scene.py` â€” Manim Scene that:
  - Shows a split or sequential before/after code view
  - Animates the transition: old code fades/slides out, new code fades/slides in
  - Highlights changed lines in green (additions) and red (deletions)
- `walkthroughs/renderer/scenes.py` â€” orchestrator that reads a walkthrough spec and chains the appropriate Scene classes together, producing a single video per spec
- Unit tests in `tests/test_renderer.py` that render a minimal spec segment and verify an mp4 file is produced

**Acceptance criteria:**
- `python -c "from walkthroughs.renderer.scenes import render_spec; render_spec('walkthroughs/specs/01_basic.yaml', audio=False)"` produces a silent video file
- Code display scenes show syntax-highlighted Python with line highlighting
- Terminal scenes show typewriter-style SQL output
- Diff scenes animate the before â†’ after transition

**Claude Code prompt:**
```
Read PLAN-phase2.md in the repo root. Implement PR 8: Manim Renderer. Create
branch 08-manim-renderer from main. Build the Manim scene classes for code
display, terminal output, and code diffs. Use a dark VS Code-inspired theme.
The renderer should consume the walkthrough YAML spec format from PR 7. Include
tests that verify video output is produced. Use conventional commits, push, and
open a PR.
```

---

### PR 9: TTS Narration & Audio-Video Compositor

**Branch:** `09-narration-compositor`
**Base:** `main` (after PR 8 merged)

**Scope:**
- `walkthroughs/narrator/generate.py`:
  - Reads a walkthrough spec's narration strings
  - Generates an audio file (.wav) per segment using Kokoro TTS (primary) or edge-tts (fallback)
  - Saves audio segments to a temp directory
- `walkthroughs/narrator/timing.py`:
  - Measures the duration of each audio segment
  - Produces a timing manifest that the renderer uses to set Manim scene durations (so animations match narration length)
- `walkthroughs/compositor/compose.py`:
  - Takes the rendered video segments (from Manim) and audio segments (from TTS)
  - Uses FFmpeg to composite: overlay audio onto video, concatenate all segments into a single output file
  - Adds brief fade transitions between segments
  - Outputs final `.mp4` to `walkthroughs/output/`
- Update `walkthroughs/cli.py`:
  - `generate` subcommand now works end-to-end: parse spec â†’ generate audio â†’ measure timing â†’ render video (with timing) â†’ composite
  - Add `--no-audio` flag to skip TTS and render silent video
  - Add `--exercise` flag to generate a specific exercise (default: all)
- Update `requirements-video.txt` with `kokoro`, `edge-tts`, `soundfile`
- Update `Makefile` with `make video`, `make video exercise=01`

**Acceptance criteria:**
- `make video exercise=01` produces `walkthroughs/output/01_basic.mp4` with both video and narration
- Audio narration is synchronized with visual segments (annotations appear as narrator describes them)
- `make video exercise=01 AUDIO=0` produces a silent version
- The timing system correctly adjusts Manim animation durations to match TTS audio lengths

**Claude Code prompt:**
```
Read PLAN-phase2.md in the repo root. Implement PR 9: TTS Narration &
Audio-Video Compositor. Create branch 09-narration-compositor from main. Use
Kokoro TTS as the primary engine with edge-tts as fallback. The key challenge
is timing synchronization â€” audio segment durations must drive Manim animation
durations. Use FFmpeg for final compositing. Update the CLI and Makefile. Use
conventional commits, push, and open a PR.
```

---

### PR 10: Complete Walkthrough Specs for Exercises 02 & 03

**Branch:** `10-remaining-walkthroughs`
**Base:** `main` (after PR 9 merged)

**Scope:**
- `walkthroughs/specs/02_intermediate.yaml` â€” full spec covering:
  - The problem: nested Category â†’ Products â†’ Variants query with N+1 at both levels
  - The fix: `prefetch_related` and `Prefetch` objects
  - Terminal output showing query reduction from ~50 to 3
  - Validation with the test harness
- `walkthroughs/specs/03_advanced.yaml` â€” full spec covering:
  - The problem: GraphQL-specific fan-out that `select_related` can't solve
  - The concept: DataLoaders and batching in Strawberry
  - Walking through `catalog/dataloaders.py`
  - Terminal output showing query reduction from ~100 to 4
  - Validation with the test harness
- Generate all three videos and verify they play correctly
- Update `exercises/README.md` to link to the video walkthroughs (or note how to generate them)

**Acceptance criteria:**
- `make video` generates all three videos end-to-end
- Each video is 3â€“5 minutes and covers the complete exercise flow
- Specs are pedagogically sound: they explain *why*, not just *what*

**Claude Code prompt:**
```
Read PLAN-phase2.md in the repo root. Implement PR 10: Complete Walkthrough
Specs for Exercises 02 & 03. Create branch 10-remaining-walkthroughs from main.
Write detailed, pedagogically sound walkthrough specs that explain the WHY
behind each fix, not just the code changes. Reference actual code from the repo.
Generate all three videos and verify output. Use conventional commits, push,
and open a PR.
```

---

### PR 11: Docker Integration & CI for Video Generation

**Branch:** `11-video-docker-ci`
**Base:** `main` (after PR 10 merged)

**Scope:**
- `Dockerfile.video` â€” a separate Dockerfile for the video pipeline (heavier image with Manim dependencies: LaTeX, FFmpeg, Cairo, Pango)
- Add a `video` service to `docker-compose.yml` (or a separate `docker-compose.video.yml`) so users can generate videos without installing Manim locally
- A GitHub Actions workflow (`.github/workflows/generate-videos.yml`) that:
  - Builds the video Docker image
  - Runs `make video` inside it
  - Uploads the generated videos as workflow artifacts
  - Optionally triggered manually or on changes to `walkthroughs/specs/*.yaml`
- Update `README.md` with instructions for generating videos via Docker and via local install
- Update `Makefile` with `make video-docker` target

**Acceptance criteria:**
- `docker compose -f docker-compose.video.yml run video make video` generates all three videos
- GitHub Actions workflow runs and produces downloadable video artifacts
- A developer without Manim installed locally can still generate videos via Docker

**Claude Code prompt:**
```
Read PLAN-phase2.md in the repo root. Implement PR 11: Docker Integration & CI
for Video Generation. Create branch 11-video-docker-ci from main. The video
Dockerfile needs Manim's system dependencies (LaTeX, Cairo, Pango, FFmpeg).
Keep it separate from the main app Dockerfile to avoid bloating the practice
environment image. Add a GitHub Actions workflow for automated generation.
Use conventional commits, push, and open a PR.
```

---

## Workflow Notes for Claude Code

1. **Always read PLAN-phase2.md first** before implementing any PR.
2. **One PR at a time.** Each PR should be merged into `main` before starting the next.
3. **Conventional commits:** `feat:`, `fix:`, `docs:`, `chore:` prefixes.
4. **Test before pushing:** verify acceptance criteria in the PR description.
5. **PR descriptions** should include: summary, acceptance criteria, test instructions, and any known limitations.
6. **Manim rendering** can be slow â€” use low quality (`-ql`) during development and high quality (`-qh`) for final output.
7. **TTS fallback** â€” if Kokoro fails to install (it needs Python 3.9â€“3.12), fall back to `edge-tts` which is pure Python with no system dependencies.

## Future Phases (Out of Scope)

- **Phase 3: Scenario Generator** â€” LLM-assisted generation of new domain models + N+1 patterns
- **Phase 4: Web UI** â€” exercise selection, progress tracking, embedded video playback
- **Phase 5: Curriculum Expansion** â€” beyond N+1: slow queries, missing indexes, query plan analysis
