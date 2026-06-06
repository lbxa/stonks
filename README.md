# stonks

`stonks` is a Python monorepo for personal stock and equity analysis. It is organized as a `uv` workspace with reusable tools in `libs/*` and valuation studies or visualizations in `apps/*`.

## Workspace Layout

- `libs/core`: shared domain primitives and return calculations.
- `libs/data`: provider-neutral market and fundamentals data interfaces.
- `libs/valuation`: DCF and multiples-based valuation helpers.
- `libs/benchmarks`: benchmark definitions for equity studies.
- `apps/notebooks`: Jupyter-based valuation studies and visualizations.

Raw market data, caches, generated reports, and local outputs are ignored by git. Keep reproducible source code and small test fixtures in the repository; keep downloaded datasets local.

## Setup

Install dependencies for every workspace member:

```bash
uv sync --all-packages
```

Resolve or refresh the shared workspace lockfile:

```bash
uv lock
```

## Common Commands

Run the full test suite:

```bash
uv run pytest
```

Lint and format:

```bash
uv run ruff check .
uv run ruff format .
```

Start Jupyter Lab for valuation studies:

```bash
uv run --package notebooks jupyter lab
```

Run the starter study script:

```bash
uv run --package notebooks python apps/notebooks/studies/company_valuation_starter.py
```

## Development Notes

Libraries should expose provider-neutral, testable building blocks. Apps can combine libraries into notebooks, reports, and visualizations. Prefer adding interfaces before hardcoding external data providers so valuation logic stays portable.
