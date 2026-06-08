---
name: python-app-structure
description: Use when creating, refactoring, reviewing, or simplifying Python uv apps/packages in the VALUE_ALPHA monorepo; choosing between flat module, package, src layout, tests, CLI entry points, pyproject/build backend, imports, or PEP-aligned file organization. Prefer simple PEP-friendly structure and avoid unnecessary app_name/src/app_name nesting unless packaging constraints require it.
---

# Python App Structure

Use this before creating or reorganizing Python code in this monorepo. This skill adapts the practical structure guidance from the Hitchhiker's Guide to Python for VALUE_ALPHA uv apps: the code of interest should be obvious, imports should reveal dependency direction, and filesystem layout should not bury a small app under repeated names.

## Default Shape

Prefer a flat single-app layout for small uv apps:

```text
apps/<app-name>/
├── pyproject.toml
├── README.md
├── <import_name>.py
└── tests/
    └── test_<behavior>.py
```

Use this when the app is a CLI, worker, script-like service, or small training/inference utility with one cohesive capability. The module is the code of interest; keep it near the app root instead of hiding it under `src`, `python`, or a duplicated app-name directory.

`pyproject.toml`:

- Use project names with hyphens: `image-classifier`.
- Use import modules with underscores: `image_classifier.py`.
- Point console scripts at the module: `image-classifier = "image_classifier:main"`.
- Use `setuptools.build_meta` with `py-modules = ["image_classifier"]` for flat modules.

Example:

```toml
[project]
name = "image-classifier"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
image-classifier = "image_classifier:main"

[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
py-modules = ["image_classifier"]
```

## When To Use A Package

Use a package folder only when the code has multiple stable subdomains or real internal boundaries:

```text
apps/<app-name>/
├── pyproject.toml
├── README.md
├── <import_name>/
│   ├── __init__.py
│   ├── cli.py
│   ├── domain.py
│   ├── application.py
│   └── infrastructure.py
└── tests/
```

Do not use `src/<import_name>/` for app-local code by default. Reserve `src` layout for distributable libraries or packages where import isolation is worth the extra path depth.

Keep package roots lightweight:

- Leave `__init__.py` empty unless the package genuinely owns a small public API.
- Do not put startup logic, I/O, dependency construction, or heavy imports in `__init__.py`.
- Prefer `import package.module` or `import very.deep.module as mod` when it makes ownership clearer.

## Organization Rules

- Follow PEP 8 names: module files use `snake_case.py`; packages use lowercase/underscore; tests use `test_*.py`.
- Keep module names short, lowercase, and importable. Never use hyphens, dots, spaces, or punctuation in `.py` file names.
- Keep CLI parsing thin. Business decisions belong in named policies, factories, repositories, gateways, or use cases.
- Prefer one file for a small coherent app. Split only when a file contains multiple stable ownership boundaries.
- Do not create `utils.py`, `helpers.py`, or `services.py` as dumping grounds.
- Prefer names that describe ownership: `CheckpointStore`, `ThresholdPolicy`, `MobileNetClassifierFactory`, `TrainClassifier`.
- Avoid one-method pass-through wrappers. Use classes only when they own policy, lifecycle, construction, external integration, persistence, or an application use case.
- Keep tests in `tests/` beside the app, not inside the package.

## Import And Coupling Rules

Treat modules as the first abstraction boundary. Split files by dependency direction and ownership, not by vague type buckets.

- Avoid `from module import *`; prefer `import module` when the module namespace makes call sites clearer.
- Avoid circular imports. If two modules need each other, the boundary is wrong; move the shared concept inward or introduce a real domain object/policy.
- Avoid hidden coupling where changes in one module break unrelated tests because another module knows too much about its internals.
- Avoid module-level mutable state for runtime context, credentials, clients, counters, caches, or workflow state. Pass dependencies explicitly or own them in a lifecycle object.
- Keep pure decision logic separate from side-effecting code when practical. This makes model policies, thresholds, transforms, and routing decisions easier to test.
- Use context managers for external resources that need cleanup. Use a class when cleanup has meaningful lifecycle logic; use `contextlib.contextmanager` for a simple scoped action.

## Decision Checklist

Before adding folders, answer:

- Is this a library reused by other packages? If yes, consider `libs/<name>/src/<import_name>/`.
- Is this an app with one executable capability? If yes, use a flat module.
- Are there multiple real subdomains with independent change paths? If yes, use a package folder.
- Would a second directory level only mirror the app name? If yes, do not add it.
- Can imports remain clear without `src`? If yes, keep the structure flat.
- Are tests forced to patch `sys.path`? If yes, prefer fixing packaging/import configuration first; only use explicit path context as a last resort.

## Validation

After restructuring:

- Run from repo root with `uv run --project apps/<app-name> pytest apps/<app-name>/tests` when the root workspace is not healthy.
- Prefer `uv run --package <package-name> ...` only when the root uv workspace is valid.
- Remove generated `.pytest_cache`, `__pycache__`, and `*.egg-info` from the app tree before finishing.

## Source Basis

This skill intentionally incorporates the Hitchhiker's Guide to Python guidance that:

- The actual module can be either a package directory or a single root-level `.py` file.
- Tests belong in `tests/` or a simple `test_*.py`, not inside the runtime package by default.
- Repetitive nesting is confusing for developers and tools.
- Python modules and namespaces are natural structure boundaries.
- Empty `__init__.py` files are normal when no package-wide API is needed.
- Unnecessary object orientation, circular dependencies, hidden coupling, global context, and many tiny near-duplicate classes are structural warning signs.
