"""CLI entry point for the walkthrough video pipeline.

Usage:
    python -m walkthroughs.cli list
    python -m walkthroughs.cli validate --spec walkthroughs/specs/01_basic.yaml
    python -m walkthroughs.cli generate --exercise 01_basic
    python -m walkthroughs.cli generate --all
    python -m walkthroughs.cli generate --exercise 01_basic --no-audio
"""

import argparse
import sys
from pathlib import Path

SPECS_DIR = Path(__file__).resolve().parent / "specs"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def cmd_list(args):
    """List available walkthrough specs."""
    specs = sorted(SPECS_DIR.glob("*.yaml"))
    if not specs:
        print("No walkthrough specs found.")
        return

    from walkthroughs.renderer import load_spec

    print(f"\nAvailable walkthroughs ({len(specs)}):\n")
    for spec_path in specs:
        try:
            spec = load_spec(spec_path)
            print(f"  {spec.exercise:20s} {spec.title}")
            print(f"  {'':20s} {len(spec.segments)} segments, target: {spec.duration_target}")
            print()
        except Exception as e:
            print(f"  {spec_path.stem:20s} ERROR: {e}")
            print()


def cmd_validate(args):
    """Validate a walkthrough spec."""
    from walkthroughs.renderer import load_spec

    spec_path = args.spec
    if not Path(spec_path).exists():
        print(f"Error: spec file not found: {spec_path}")
        sys.exit(1)

    try:
        spec = load_spec(spec_path)
        print(f"Valid: {spec.exercise} — {spec.title}")
        print(f"  Segments: {len(spec.segments)}")
        for i, seg in enumerate(spec.segments):
            print(f"    [{i}] {seg.type}: {seg.narration[:60]}...")
        print("\nAll checks passed.")
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)


def cmd_generate(args):
    """Generate walkthrough video(s)."""
    from walkthroughs.renderer import load_spec
    from walkthroughs.renderer.scenes import render_spec
    from walkthroughs.narrator.generate import generate_narration
    from walkthroughs.narrator.timing import calculate_durations
    from walkthroughs.compositor.compose import compose_walkthrough

    quality = args.quality or "low"
    no_audio = args.no_audio

    # Determine which specs to build
    if args.all:
        spec_files = sorted(SPECS_DIR.glob("*.yaml"))
    elif args.exercise:
        spec_file = SPECS_DIR / f"{args.exercise}.yaml"
        if not spec_file.exists():
            # Try without extension
            candidates = list(SPECS_DIR.glob(f"*{args.exercise}*.yaml"))
            if candidates:
                spec_file = candidates[0]
            else:
                print(f"Error: no spec found for exercise '{args.exercise}'")
                sys.exit(1)
        spec_files = [spec_file]
    else:
        print("Error: specify --exercise or --all")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for spec_path in spec_files:
        spec = load_spec(spec_path)
        print(f"\n{'='*60}")
        print(f"Generating: {spec.exercise} — {spec.title}")
        print(f"{'='*60}")

        audio_dir = OUTPUT_DIR / f"{spec.exercise}_audio"

        # Step 1: Generate audio (unless --no-audio)
        if no_audio:
            print("\nSkipping audio generation (--no-audio)")
            audio_files = [None] * len(spec.segments)
            durations = None
        else:
            print("\nStep 1: Generating narration audio...")
            audio_files = generate_narration(spec.segments, audio_dir)
            print("\nStep 2: Calculating segment timing from audio...")
            durations = calculate_durations(audio_files)
            for i, (d, seg) in enumerate(zip(durations, spec.segments)):
                print(f"  Segment {i} ({seg.type}): {d:.1f}s")

        # Step 2/3: Render video segments
        step = "Step 2" if no_audio else "Step 3"
        print(f"\n{step}: Rendering video segments (quality={quality})...")
        video_segments = render_spec(
            spec_path,
            output_dir=OUTPUT_DIR,
            quality=quality,
            durations=durations,
        )

        # Step 3/4: Composite
        step = "Step 3" if no_audio else "Step 4"
        final_output = OUTPUT_DIR / f"{spec.exercise}.mp4"
        print(f"\n{step}: Compositing final video...")
        compose_walkthrough(video_segments, audio_files, final_output)

        print(f"\nDone! Output: {final_output}")
        print(f"  Size: {final_output.stat().st_size / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="N+1 Query Practice — Walkthrough Video Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list
    subparsers.add_parser("list", help="List available walkthrough specs")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a spec file")
    validate_parser.add_argument("--spec", required=True, help="Path to YAML spec file")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate walkthrough video(s)")
    gen_parser.add_argument("--exercise", help="Exercise name (e.g., 01_basic)")
    gen_parser.add_argument("--all", action="store_true", help="Generate all walkthroughs")
    gen_parser.add_argument("--no-audio", action="store_true", help="Skip TTS narration")
    gen_parser.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        default="low",
        help="Video quality (default: low)",
    )

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "generate":
        cmd_generate(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
