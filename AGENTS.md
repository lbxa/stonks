# Repository Guidelines

## Project Structure & Module Organization

This is a `uv` workspace for personal stock and equity analysis. Reusable packages live in `libs/*`: `core` for primitives, `data` for provider-neutral data interfaces, `valuation` for valuation models, and `benchmarks` for comparison baselines. Studies and visualizations live in `apps/*`, starting with `apps/notebooks`.

Each library uses a `src/<package>` layout and keeps tests in its local `tests/` directory. Keep raw downloads, caches, generated reports, and notebook checkpoints out of git.

## Build, Test, and Development Commands

- `uv sync --all-packages` installs all workspace members.
- `uv lock` resolves the shared workspace lockfile.
- `uv run pytest` runs all tests.
- `uv run ruff check .` lints the repository.
- `uv run ruff format .` formats Python files.
- `uv run --package notebooks jupyter lab` starts the notebook app.
- `uv run --package notebooks python apps/notebooks/studies/company_valuation_starter.py` runs the starter study.

## Coding Style & Naming Conventions

Use Python 3.12 or newer. Follow PEP 8 with 4-space indentation, `snake_case` functions and variables, `PascalCase` classes, and lowercase module names. Keep package APIs small and importable from each package’s `__init__.py` only when they are stable.

Ruff is the formatter and linter. Prefer typed dataclasses and small pure functions for valuation logic so calculations are easy to test.

## Testing Guidelines

Use `pytest`. Name files `test_*.py` and functions `test_*`. Put tests next to the workspace member they cover, for example `libs/valuation/tests/test_valuation.py`.

Add regression tests for valuation formulas, provider adapters, benchmark definitions, and data normalization rules. Tests should not require network access or live market data.

## Commit & Pull Request Guidelines

This repository has no established commit history yet. Use short imperative commit messages such as `Add DCF model` or `Create notebook workspace`.

Pull requests should include a concise summary, testing performed, and any assumptions about data sources. Include screenshots or exported examples when changing notebooks, reports, or visualizations.

## Security & Configuration Tips

Do not commit API keys, downloaded datasets, local caches, or generated reports. Put future provider credentials in environment variables or ignored local config files.

## Agent-Specific Instructions

Inspect current files before editing and preserve unrelated user changes. Use Context7 for current library, framework, SDK, API, CLI, or cloud-service documentation. Keep changes scoped and update this guide whenever workspace commands or structure change.
