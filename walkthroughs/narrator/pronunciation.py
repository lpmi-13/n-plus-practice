"""Pronunciation preprocessing for technical narration text.

Converts code-like terms (e.g., `.all()`, `select_related`, `__`)
into speakable forms before sending text to TTS engines.

The dictionary can be extended manually or by running the audit tool:
    python -m walkthroughs.narrator.audit_pronunciation
"""

import re

# Ordered list of (pattern, replacement) tuples.
# Order matters: more specific patterns should come before general ones.
# Patterns are compiled regexes; replacements are plain strings or callables.
PRONUNCIATION_RULES: list[tuple[re.Pattern, str]] = [
    # === Method calls & attribute access (specific before general) ===
    (re.compile(r"\.objects\.all\b"), " dot objects dot all"),
    (re.compile(r"\.objects\.filter\b"), " dot objects dot filter"),
    (re.compile(r"\.select_related\("), " dot select related("),
    (re.compile(r"\.prefetch_related\("), " dot prefetch related("),
    (re.compile(r"\.all\(\)"), " dot all"),
    (re.compile(r"\.load\b"), " dot load"),
    (re.compile(r"\.save\b"), " dot save"),

    # === Django/Python dunder & underscore patterns ===
    (re.compile(r"__in\b"), " in"),
    (re.compile(r"(\w)__(\w)"), r"\1 double underscore \2"),
    (re.compile(r"(\w)_(\w)"), r"\1 \2"),

    # === Specific technical terms (case-insensitive where needed) ===
    (re.compile(r"\bselect_related\b"), "select related"),
    (re.compile(r"\bprefetch_related\b"), "prefetch related"),
    (re.compile(r"\bcategory_id\b"), "category ID"),
    (re.compile(r"\bproduct_id\b"), "product ID"),
    (re.compile(r"\bauthor_id\b"), "author ID"),
    (re.compile(r"\bDataLoaders\b"), "data loaders"),
    (re.compile(r"\bDataLoader\b"), "data loader"),
    (re.compile(r"\bQuerySet\b"), "query set"),
    (re.compile(r"\bqueryset\b"), "query set"),
    (re.compile(r"\bProductType\b"), "Product Type"),
    (re.compile(r"\bCategoryType\b"), "Category Type"),
    (re.compile(r"\bReviewType\b"), "Review Type"),
    (re.compile(r"\bAuthorType\b"), "Author Type"),
    (re.compile(r"\bVariantType\b"), "Variant Type"),
    (re.compile(r"\bForeignKey\b"), "foreign key"),
    (re.compile(r"\bOneToOneField\b"), "one-to-one field"),
    (re.compile(r"\bManyToMany\b"), "many-to-many"),
    (re.compile(r"\bGraphQL\b"), "Graph Q L"),
    (re.compile(r"\bgraphql\b", re.IGNORECASE), "Graph Q L"),
    (re.compile(r"\bORM\b"), "O R M"),
    (re.compile(r"\bSQL\b"), "S Q L"),
    (re.compile(r"\bAPI\b"), "A P I"),
    (re.compile(r"\bAPIs\b"), "A P Is"),
    (re.compile(r"\bFK\b"), "foreign key"),
    (re.compile(r"\bID\b"), "I D"),
    (re.compile(r"\bIDs\b"), "I Ds"),
    (re.compile(r"\bN\s*\+\s*1\b"), "N plus one"),
    (re.compile(r"\bN\+1\b"), "N plus one"),

    # === Punctuation in code references ===
    (re.compile(r"self\.(\w+)\.(\w+)"), r"self dot \1 dot \2"),
    (re.compile(r"self\.(\w+)"), r"self dot \1"),
    (re.compile(r"(\w+)\.(\w+)\.(\w+)"), r"\1 dot \2 dot \3"),
]

# Simple string replacements applied before regex rules.
# Use for exact tokens that don't need pattern matching.
EXACT_REPLACEMENTS: dict[str, str] = {
    "psycopg2": "sigh-cop-gee two",
    "Django": "Jango",
    "django": "Jango",
    "<=": "less than or equal to",
    ">=": "greater than or equal to",
    "31x": "thirty-one times",
}


def preprocess_narration(text: str) -> str:
    """Apply pronunciation rules to narration text.

    Transforms code-like terms into speakable forms suitable for TTS.
    The original narration text in specs stays clean and readable;
    this function is applied just before passing text to the TTS engine.

    Args:
        text: Raw narration text from a walkthrough spec.

    Returns:
        Text with technical terms converted to speakable forms.
    """
    # Apply exact string replacements first
    for original, replacement in EXACT_REPLACEMENTS.items():
        text = text.replace(original, replacement)

    # Apply regex rules in order
    for pattern, replacement in PRONUNCIATION_RULES:
        text = pattern.sub(replacement, text)

    # Clean up any double spaces introduced by replacements
    text = re.sub(r"  +", " ", text)

    return text.strip()
