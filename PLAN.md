# N+1 Query Practice Environment — MVP Implementation Plan

## Repository

https://github.com/lpmi-13/n-plus-practice

## Project Overview

A hands-on learning environment where junior developers can identify and fix N+1 query problems in a Django + GraphQL codebase. The MVP delivers a containerized practice app with deliberate N+1 problems, a query-counting harness for validation, and guided exercises with progressive difficulty.

This plan is designed to be executed as a sequence of pull requests using Claude Code.

---

## Architecture Decisions

### Stack
- **Python 3.12** + **Django 5.x** + **Strawberry GraphQL** (type-safe, modern, good DX over Graphene)
- **PostgreSQL 16** as the database (realistic query behavior vs SQLite)
- **Docker Compose** for the full environment (Django app + Postgres)
- **django-debug-toolbar** + **django-query-counter** for N+1 visibility
- **pytest** + **django-test-plus** for the validation harness

### Domain Model
A small e-commerce catalog — rich enough to produce real N+1 patterns, simple enough to grok quickly:

```
Category → Product → Variant (size/color)
                   → Review (with author)
Author → Review
```

This gives us:
- One-to-many (Category → Products)
- One-to-many (Product → Variants)
- One-to-many (Product → Reviews)
- Foreign key (Review → Author)
- Nested traversal (Category → Product → Review → Author)

### Project Layout

```
repo-root/
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── manage.py
├── config/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── catalog/                 # Main app
│   ├── models.py
│   ├── schema.py            # Strawberry GraphQL schema
│   ├── dataloaders.py       # DataLoader implementations (used in fixes)
│   ├── admin.py
│   └── management/
│       └── commands/
│           └── seed_db.py   # Seed data generator
├── exercises/               # Exercise definitions
│   ├── README.md            # Exercise guide with progressive difficulty
│   ├── 01_basic/
│   │   ├── BRIEF.md         # Problem description + hints
│   │   └── solution.md      # Worked solution
│   ├── 02_intermediate/
│   │   ├── BRIEF.md
│   │   └── solution.md
│   └── 03_advanced/
│       ├── BRIEF.md
│       └── solution.md
└── tests/
    ├── conftest.py
    └── test_query_counts.py # Validation harness — asserts query counts
```

---

## PR Breakdown

### PR 1: Project Skeleton & Docker Setup

**Branch:** `01-project-skeleton`

**Scope:**
- `Dockerfile` (Python 3.12 slim, install deps, copy app)
- `docker-compose.yml` (Django web service + Postgres service, exposed ports, volume for DB persistence)
- `requirements.txt` (Django, Strawberry, psycopg2-binary, django-extensions)
- Django project scaffolding via `django-admin startproject config .`
- `config/settings.py` configured for Postgres (read from env vars), installed apps
- `config/urls.py` with Strawberry GraphQL view mounted at `/graphql`
- Minimal `catalog/` app with empty `models.py` and a hello-world schema
- `README.md` with setup instructions (clone, `docker compose up`, visit `/graphql`)
- `.gitignore` for Python/Django/Docker

**Acceptance criteria:**
- `docker compose up` starts both services
- Visiting `http://localhost:8000/graphql` shows the Strawberry GraphiQL explorer
- A trivial query like `{ hello }` returns a response

**Claude Code prompt:**
```
Read PLAN.md in the repo root. Implement PR 1: Project Skeleton & Docker Setup.
Create a new branch 01-project-skeleton from main. Follow the architecture
decisions and project layout exactly. Commit with conventional commits.
When done, push the branch and open a PR with a description summarizing what
was added and how to test it.
```

---

### PR 2: Domain Models & Seed Data

**Branch:** `02-models-and-seeds`
**Base:** `main` (after PR 1 is merged)

**Scope:**
- `catalog/models.py` — Category, Product, Variant, Author, Review models with proper foreign keys and `related_name` attributes
- `catalog/admin.py` — register all models for Django admin
- Migration files via `makemigrations`
- `catalog/management/commands/seed_db.py` — management command that creates ~5 categories, ~30 products, ~60 variants, ~10 authors, ~100 reviews with realistic fake data (use `random` + hardcoded lists, no Faker dependency needed)
- Update `README.md` with seed instructions

**Acceptance criteria:**
- `docker compose exec web python manage.py migrate` runs clean
- `docker compose exec web python manage.py seed_db` populates the database
- Django admin at `/admin` shows all models with data

**Claude Code prompt:**
```
Read PLAN.md in the repo root. Implement PR 2: Domain Models & Seed Data.
Create branch 02-models-and-seeds from main. Follow the domain model from the
plan. The seed command should be idempotent (clear + recreate). Use conventional
commits. Push and open a PR.
```

---

### PR 3: GraphQL Schema with Deliberate N+1 Problems

**Branch:** `03-graphql-schema-broken`
**Base:** `main` (after PR 2 is merged)

**Scope:**
- `catalog/schema.py` — Strawberry types for all models, with **deliberately naive resolvers** that trigger N+1 queries:
  - `CategoryType.products` → `self.products.all()` (triggers N+1 when listing categories)
  - `ProductType.variants` → `self.variants.all()`
  - `ProductType.reviews` → `self.reviews.all()`
  - `ReviewType.author` → `self.author` (lazy FK load)
  - `ProductType.average_rating` → computed via Python loop over `self.reviews.all()`
- Root queries: `categories`, `products`, `product(id)` — all using bare `.all()` querysets with no `select_related` or `prefetch_related`
- Add `django-extensions` and enable `LOGGING` in settings to print SQL queries to console (so learners can see the N+1 in real time)

**Acceptance criteria:**
- A query like `{ categories { name products { name reviews { text author { name } } } } }` works but produces 50+ SQL queries visible in the console
- The GraphiQL explorer is usable for exploring the schema

**Claude Code prompt:**
```
Read PLAN.md in the repo root. Implement PR 3: GraphQL Schema with Deliberate
N+1 Problems. Create branch 03-graphql-schema-broken from main. The resolvers
MUST be naive — no select_related, no prefetch_related, no DataLoaders. These
are the bugs the learner will fix. Enable SQL query logging to stdout so the
query count is visible. Push and open a PR.
```

---

### PR 4: Query-Counting Validation Harness

**Branch:** `04-validation-harness`
**Base:** `main` (after PR 3 is merged)

**Scope:**
- `tests/conftest.py` — pytest fixtures for seeded DB, GraphQL client, and a `query_counter` context manager that captures Django DB query count
- `tests/test_query_counts.py` — test cases that:
  - Execute specific GraphQL queries
  - Assert the current (broken) query count is high (e.g., `assert count > 20`)
  - Include commented-out "target" assertions (e.g., `# GOAL: assert count <= 4`) that the learner un-comments after fixing
- A helper script or management command `check_queries` that runs a specific query and prints "You used N queries. Target: M."
- Update `requirements.txt` with pytest, pytest-django

**Acceptance criteria:**
- `docker compose exec web pytest` runs and all tests pass (against the broken schema)
- The tests clearly document what the target query count should be
- The `check_queries` helper gives immediate feedback

**Claude Code prompt:**
```
Read PLAN.md in the repo root. Implement PR 4: Query-Counting Validation
Harness. Create branch 04-validation-harness from main. The tests should pass
against the current broken schema (asserting high query counts). Include
commented-out target assertions. The check_queries command should accept a
query name argument and print current vs target count. Push and open a PR.
```

---

### PR 5: Exercise Guides (Progressive Difficulty)

**Branch:** `05-exercise-guides`
**Base:** `main` (after PR 4 is merged)

**Scope:**
- `exercises/README.md` — overview of the learning path, how to use the environment, how to check your work
- `exercises/01_basic/BRIEF.md` — **"Fix the product listing"**
  - Problem: listing products with their category triggers N+1
  - Skill: `select_related` on FK fields
  - Hints: point to Django docs, show how to read the SQL log
  - Target: reduce from ~30 queries to 1
- `exercises/01_basic/solution.md` — worked solution with explanation
- `exercises/02_intermediate/BRIEF.md` — **"Fix the category → products → variants query"**
  - Problem: nested prefetching needed
  - Skill: `prefetch_related`, `Prefetch` objects
  - Target: reduce from ~50 queries to 3
- `exercises/02_intermediate/solution.md`
- `exercises/03_advanced/BRIEF.md` — **"Fix the GraphQL nested query with DataLoaders"**
  - Problem: GraphQL-specific fan-out that `select_related` can't solve
  - Skill: Strawberry DataLoaders, batching
  - Includes `catalog/dataloaders.py` as a starting scaffold
  - Target: reduce from ~100 queries to 4
- `exercises/03_advanced/solution.md`
- Update root `README.md` with learning path overview

**Acceptance criteria:**
- Each exercise brief clearly states the problem, the skill to learn, and the target query count
- Solutions are complete and actually achieve the stated targets
- A learner can follow the path from exercise 1 → 3 without confusion

**Claude Code prompt:**
```
Read PLAN.md in the repo root. Implement PR 5: Exercise Guides. Create branch
05-exercise-guides from main. Write clear, pedagogically sound exercise briefs
and solutions. Solutions must include actual code changes and explain WHY each
fix works. Reference the test harness from PR 4 for validation. Push and open
a PR.
```

---

### PR 6: Polish — README, DX, Quick Start

**Branch:** `06-polish`
**Base:** `main` (after PR 5 is merged)

**Scope:**
- Comprehensive `README.md` rewrite: project purpose, prerequisites, quick start (3 commands), learning path, how to validate, troubleshooting
- `Makefile` or shell scripts for common commands (`make setup`, `make seed`, `make test`, `make check exercise=01`)
- Add Django query logging toggle (env var `SHOW_SQL=1`) so learners can turn it on/off
- Verify the full flow end-to-end: clone → docker compose up → seed → explore → break → exercise → fix → validate

**Acceptance criteria:**
- A junior developer can clone the repo and be working on exercise 1 within 5 minutes
- All make targets work
- README is clear and welcoming

**Claude Code prompt:**
```
Read PLAN.md in the repo root. Implement PR 6: Polish. Create branch 06-polish
from main. Focus on developer experience — a junior dev should be able to go
from clone to first exercise in under 5 minutes. Add a Makefile with intuitive
targets. Push and open a PR.
```

---

## Workflow Notes for Claude Code

1. **Always read PLAN.md first** before implementing any PR.
2. **One PR at a time.** Each PR should be merged into `main` before starting the next.
3. **Conventional commits:** `feat:`, `fix:`, `docs:`, `chore:` prefixes.
4. **Test before pushing:** run `docker compose up` and verify acceptance criteria.
5. **PR descriptions** should summarize changes, list acceptance criteria, and include test instructions.

## Future PRs (Post-MVP)

These are out of scope for now but planned for later:
- Scenario generator for additional domain models
- Video walkthrough pipeline (screen recording + TTS narration)
- Web UI for exercise selection and progress tracking
- Additional exercise topics beyond N+1 (slow queries, missing indexes, etc.)
