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

## Toggling SQL Logging

SQL query logging is controlled by the `SHOW_SQL` environment variable in `docker-compose.yml`. Set it to `"0"` to disable the query output.

## Stack

- Python 3.12 + Django 5.x + Strawberry GraphQL
- PostgreSQL 16
- Docker Compose
