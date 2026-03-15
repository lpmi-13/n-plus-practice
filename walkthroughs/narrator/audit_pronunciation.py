"""Audit narration text from walkthrough specs for pronunciation issues.

Extracts all narration from YAML specs, identifies tokens that look like
code or technical terms, and reports which ones are NOT yet covered by
the pronunciation dictionary.  This helps you build up the dictionary
incrementally as new specs are added.

Usage:
    python -m walkthroughs.narrator.audit_pronunciation
    python -m walkthroughs.narrator.audit_pronunciation --spec walkthroughs/specs/01_basic.yaml
    python -m walkthroughs.narrator.audit_pronunciation --show-transformed
"""

import argparse
import re
import sys
from pathlib import Path

from walkthroughs.narrator.pronunciation import (
    EXACT_REPLACEMENTS,
    PRONUNCIATION_RULES,
    preprocess_narration,
)
from walkthroughs.renderer import load_spec

SPECS_DIR = Path(__file__).resolve().parent.parent / "specs"

# ── Heuristic detectors ────────────────────────────────────────────
# Each detector returns a list of (token, reason) tuples for things
# that *look like* they need special pronunciation handling.

# Tokens that look like they need pronunciation rules but actually
# don't — TTS engines pronounce these correctly as English words.
_FALSE_POSITIVES = frozenset({
    "IN", "JOIN", "INNER", "SELECT", "FROM", "WHERE", "AND", "OR",
    "ON", "AS", "BY", "IS", "NOT", "NULL", "ALL", "LEFT", "RIGHT",
    "OUTER", "GROUP", "ORDER", "HAVING", "LIMIT", "OFFSET", "INSERT",
    "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "TABLE", "INDEX",
    "PASS", "NEEDS", "FIX",
})

_DETECTORS: list[tuple[str, re.Pattern]] = [
    ("dotted attribute access", re.compile(r"\b\w+\.\w+(?:\.\w+)*(?:\(\))?", re.ASCII)),
    ("snake_case identifier", re.compile(r"\b[a-z]\w*_\w+\b", re.ASCII)),
    ("CamelCase identifier", re.compile(r"\b[A-Z][a-z]+[A-Z]\w*\b", re.ASCII)),
    ("ALL_CAPS acronym/constant", re.compile(r"\b[A-Z]{2,}\b", re.ASCII)),
    ("dunder pattern", re.compile(r"\b\w+__\w+\b", re.ASCII)),
    ("method call with parens", re.compile(r"\.\w+\(\)", re.ASCII)),
    ("operator expression", re.compile(r"\b\w+\s*[+\-*/]=?\s*\d+\b", re.ASCII)),
    ("comparison operator", re.compile(r"[<>]=?\s*\d+", re.ASCII)),
    ("numeric with suffix", re.compile(r"\b\d+[a-zA-Z]+\b", re.ASCII)),
]


def _is_covered(token: str) -> bool:
    """Check whether a token is already handled by pronunciation rules."""
    # Check exact replacements
    if token in EXACT_REPLACEMENTS:
        return True

    # Check if any regex rule matches this token
    for pattern, _replacement in PRONUNCIATION_RULES:
        if pattern.search(token):
            return True

    return False


def _extract_narration_texts(spec_path: Path) -> list[dict]:
    """Extract all narration text from a spec with metadata."""
    spec = load_spec(spec_path)
    results = []
    for i, segment in enumerate(spec.segments):
        narration = segment.narration.strip()
        if narration:
            results.append({
                "spec": spec.exercise,
                "segment_index": i,
                "segment_type": segment.type,
                "text": narration,
            })
    return results


def _detect_candidates(text: str) -> list[tuple[str, str]]:
    """Find tokens in text that look like they need pronunciation rules.

    Returns:
        List of (token, reason) tuples.
    """
    candidates = []
    seen = set()

    for reason, pattern in _DETECTORS:
        for match in pattern.finditer(text):
            token = match.group()
            if token not in seen and token not in _FALSE_POSITIVES:
                seen.add(token)
                candidates.append((token, reason))

    return candidates


def audit_specs(
    spec_paths: list[Path] | None = None,
    show_transformed: bool = False,
) -> dict:
    """Audit specs and return a report of pronunciation gaps.

    Args:
        spec_paths: Specific specs to audit. If None, audits all.
        show_transformed: Also print before/after for each narration.

    Returns:
        Dict with 'covered', 'uncovered', and 'stats' keys.
    """
    if spec_paths is None:
        spec_paths = sorted(SPECS_DIR.glob("*.yaml"))

    all_narrations = []
    for path in spec_paths:
        all_narrations.extend(_extract_narration_texts(path))

    covered: dict[str, list[str]] = {}      # token → [reasons]
    uncovered: dict[str, list[str]] = {}     # token → [reasons]
    occurrences: dict[str, list[str]] = {}   # token → [spec:segment locations]

    for entry in all_narrations:
        candidates = _detect_candidates(entry["text"])
        location = f"{entry['spec']}:segment_{entry['segment_index']}"

        for token, reason in candidates:
            occurrences.setdefault(token, []).append(location)

            if _is_covered(token):
                covered.setdefault(token, []).append(reason)
            else:
                uncovered.setdefault(token, []).append(reason)

    report = {
        "covered": covered,
        "uncovered": uncovered,
        "occurrences": occurrences,
        "narrations": all_narrations,
        "stats": {
            "total_specs": len(spec_paths),
            "total_segments": len(all_narrations),
            "total_candidates": len(covered) + len(uncovered),
            "covered_count": len(covered),
            "uncovered_count": len(uncovered),
        },
    }

    return report


def print_report(report: dict, show_transformed: bool = False) -> None:
    """Print a human-readable audit report."""
    stats = report["stats"]

    print(f"\n{'=' * 70}")
    print("  Pronunciation Audit Report")
    print(f"{'=' * 70}")
    print(f"\n  Specs audited:       {stats['total_specs']}")
    print(f"  Segments with text:  {stats['total_segments']}")
    print(f"  Candidate tokens:    {stats['total_candidates']}")
    print(f"  Already covered:     {stats['covered_count']}")
    print(f"  NOT covered:         {stats['uncovered_count']}")

    if report["uncovered"]:
        print(f"\n{'─' * 70}")
        print("  UNCOVERED — consider adding to pronunciation.py:\n")

        # Sort by number of occurrences (most frequent first)
        sorted_uncovered = sorted(
            report["uncovered"].items(),
            key=lambda kv: len(report["occurrences"].get(kv[0], [])),
            reverse=True,
        )

        for token, reasons in sorted_uncovered:
            locations = report["occurrences"].get(token, [])
            unique_reasons = sorted(set(reasons))
            print(f"  {token!r:40s}  ({', '.join(unique_reasons)})")
            for loc in locations[:3]:  # Show first 3 locations
                print(f"    └─ {loc}")
            if len(locations) > 3:
                print(f"    └─ ...and {len(locations) - 3} more")

    if report["covered"]:
        print(f"\n{'─' * 70}")
        print(f"  COVERED ({stats['covered_count']} tokens handled by existing rules)\n")

        for token in sorted(report["covered"]):
            print(f"    ✓ {token!r}")

    if show_transformed:
        print(f"\n{'─' * 70}")
        print("  BEFORE / AFTER transformation:\n")

        for entry in report["narrations"]:
            original = entry["text"]
            transformed = preprocess_narration(original)
            if original != transformed:
                print(f"  [{entry['spec']}:segment_{entry['segment_index']}]")
                print(f"    BEFORE: {original[:120]}...")
                print(f"    AFTER:  {transformed[:120]}...")
                print()

    print(f"\n{'=' * 70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Audit walkthrough narration for pronunciation gaps"
    )
    parser.add_argument(
        "--spec",
        help="Path to a specific YAML spec to audit (default: all)",
    )
    parser.add_argument(
        "--show-transformed",
        action="store_true",
        help="Show before/after transformation for each narration",
    )

    args = parser.parse_args()

    spec_paths = None
    if args.spec:
        path = Path(args.spec)
        if not path.exists():
            print(f"Error: spec not found: {args.spec}")
            sys.exit(1)
        spec_paths = [path]

    report = audit_specs(spec_paths)
    print_report(report, show_transformed=args.show_transformed)

    # Exit with non-zero if there are uncovered tokens
    if report["uncovered"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
