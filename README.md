# N+1 Query Practice Environment

A hands-on learning environment where you can identify and fix N+1 query problems in a Django + GraphQL codebase.

## What You'll Learn

- How to spot N+1 queries using SQL logging
- Using `select_related` for ForeignKey joins
- Using `prefetch_related` for reverse relations
- Implementing GraphQL DataLoaders for batched queries

## Quick Start

```bash
# 1. Clone and start
git clone https://github.com/lpmi-13/n-plus-practice.git
cd n-plus-practice

# 2. Build, migrate, and seed (one command)
make setup

# 3. Open the GraphQL explorer
open http://localhost:8000/graphql
```

That's it. You're ready to start the exercises.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

## Exercises

Work through these in order — each builds on the previous one:

| # | Difficulty | What You'll Fix | Skill |
|---|-----------|-----------------|-------|
| 01 | Basic | Product → Category | `select_related` |
| 02 | Intermediate | Category → Products → Variants | `prefetch_related` |
| 03 | Advanced | Full-depth nested query | DataLoaders |

Start with [exercises/01_basic/BRIEF.md](exercises/01_basic/BRIEF.md).

## Validating Your Fixes

```bash
# Check a specific query
make check q=products_with_category

# Check all queries
make check

# Run the full test suite
make test
```

## Try a Query

Paste this into the GraphiQL explorer and watch the SQL queries in the console:

```graphql
{
  categories {
    name
    products {
      name
      reviews {
        text
        author {
          name
        }
      }
    }
  }
}
```

You'll see dozens of SQL queries scroll by. Your goal is to reduce them to a handful.

## Available Commands

| Command | Description |
|---------|-------------|
| `make setup` | Build, migrate, and seed everything |
| `make start` | Start containers |
| `make stop` | Stop containers |
| `make seed` | Re-seed the database |
| `make test` | Run the test suite |
| `make check` | Check query counts for all exercises |
| `make check q=NAME` | Check a specific query |
| `make logs` | Tail the web container logs |
| `make shell` | Open a Django shell |
| `make video` | Generate all walkthrough videos |
| `make video exercise=NAME` | Generate a specific walkthrough |
| `make video-silent` | Generate videos without audio |
| `make video-hq` | Generate high-quality (1080p) videos |
| `make video-kokoro` | Generate videos using Kokoro TTS |
| `make audit-pronunciation` | Audit narration for pronunciation gaps |

## Toggling SQL Logging

SQL query logging is controlled by the `SHOW_SQL` environment variable in `docker-compose.yml`. Set it to `"0"` to disable the query output.

## Video Walkthroughs

Each exercise has an auto-generated video walkthrough with narration. The pipeline reads YAML specs from `walkthroughs/specs/`, renders animated scenes with Manim, generates spoken narration via TTS, and composites the final video with FFmpeg.

### Prerequisites

Install the video pipeline dependencies (in addition to the main app):

```bash
pip install -r requirements-video.txt
```

To use the local Kokoro TTS engine instead of edge-tts, also install:

```bash
pip install kokoro>=0.8 numpy
```

### Generating Videos

```bash
# Generate all walkthrough videos (uses edge-tts by default)
make video

# Generate a specific exercise
make video exercise=01_basic

# Generate without audio (silent, for fast iteration)
make video-silent

# Generate in high quality (1080p)
make video-hq

# Generate using Kokoro TTS (local, no internet needed)
make video-kokoro
make video-kokoro exercise=01_basic
```

Or use the CLI directly for more control:

```bash
# List available walkthrough specs
python -m walkthroughs.cli list

# Validate a spec
python -m walkthroughs.cli validate --spec walkthroughs/specs/01_basic.yaml

# Generate with specific options
python -m walkthroughs.cli generate \
  --exercise 01_basic \
  --tts-backend kokoro \
  --voice af_heart \
  --speed 0.9 \
  --quality medium
```

Output videos are written to `walkthroughs/output/`.

### Pronunciation Preprocessing

Technical narration needs special handling — terms like `.all()`, `select_related`, and `N+1` must be converted to speakable forms before TTS synthesis. The pronunciation module (`walkthroughs/narrator/pronunciation.py`) handles this automatically.

To audit your specs for terms that aren't yet covered by the pronunciation dictionary:

```bash
# Scan all specs and report uncovered terms
make audit-pronunciation

# Audit a single spec
python -m walkthroughs.cli audit-pronunciation --spec walkthroughs/specs/01_basic.yaml

# See before/after text transformation for every narration segment
python -m walkthroughs.cli audit-pronunciation --show-transformed
```

The audit tool uses heuristics to detect code-like tokens (dotted access, snake_case, CamelCase, acronyms, etc.) and checks whether they're covered by existing pronunciation rules. When adding new specs, run the audit to discover terms that need dictionary entries, then add them to `PRONUNCIATION_RULES` or `EXACT_REPLACEMENTS` in `pronunciation.py`.

### TTS Backend Comparison

| Feature | edge-tts (default) | Kokoro |
|---------|-------------------|--------|
| Requires internet | Yes | No |
| API key needed | No | No |
| Output format | MP3 | WAV |
| Voice quality | Good (neural) | Good (StyleTTS2) |
| Speed control | No | Yes (`--speed`) |
| Install size | Tiny | ~200MB (model weights) |

### Pipeline Architecture

```
YAML Spec → Pronunciation Preprocessing → TTS Audio → Timing Calculation
                                                            ↓
                                                    Manim Rendering
                                                            ↓
                                                  FFmpeg Compositing
                                                            ↓
                                                     Final MP4 Video
```

## Stack

- Python 3.12 + Django 5.x + Strawberry GraphQL
- PostgreSQL 16
- Docker Compose
