# Junie Guidelines for Wolfie3D

This file provides guidance for JetBrains IDEs with Junie integration. It helps AI assistants (Junie and others) understand the context of this project and collaborate effectively.

## Project Overview

* **Name:** Wolfie3D
* **Description:** Pygame-based 3D shooter (currently scaffolding and tooling only).
* **Language:** Python 3.10+
* **Dependency Manager:** [uv](https://docs.astral.sh/uv/) (required)
* **Structure:**

  * `src/wolfie3d/` — core package
  * `tests/` — unit and integration tests
  * `assets/` — game assets (models, textures, sounds, shaders)
  * `docs/` — design notes and documentation
  * `scripts/` — helper scripts

## Development Workflow

1. **Install dependencies**

   ```bash
   uv sync --dev
   ```

2. **Run common checks**

   ```bash
   uv run python -m ruff check .
   uv run python -m mypy src
   uv run python -m pytest
   ```

3. **Format code**

   ```bash
   uv run python -m black .
   ```

4. **Coverage**

   ```bash
   PYTHONPATH=src uv run python -m pytest --cov --cov-report=term-missing
   ```

5. **Pre-commit**

   ```bash
   uv run python -m pre_commit run --all-files || uv run python -m pre-commit run --all-files
   ```

## Coding Guidelines

* **Style:**

  * Black (formatting)
  * Ruff (linting)
  * Mypy (type checking, strict mode)
* **Tests:** All code in `src/` must have corresponding tests in `tests/`.
* **Structure:** Keep functions small, modular, and well-documented.
* **Dependencies:**

  * Runtime deps in `project.dependencies`.
  * Dev tools in `[dependency-groups].dev`.

## Collaboration Guidelines

* **Commit Messages:**

  * Use [conventional commits](https://www.conventionalcommits.org/) style where possible: `feat:`, `fix:`, `chore:`, `docs:`, `test:`.
  * Keep them clear and scoped.

* **Branches:**

  * `main`: protected, stable.
  * `feat/*`, `fix/*`, `chore/*`, `docs/*`: for work branches.

* **Pull Requests:**

  * Must pass lint, type checks, and tests before review.
  * Include rationale for changes.

## Junie/AI Agent Instructions

* **When suggesting code:**

  * Follow Black/Ruff/Mypy rules.
  * Place new code in `src/wolfie3d/` or `tests/` as appropriate.
  * Respect existing project structure.

* **When writing tests:**

  * Use `pytest` style.
  * Mirror package layout in `tests/`.

* **When updating dependencies:**

  * Add runtime deps under `[project.dependencies]`.
  * Add dev tools under `[dependency-groups].dev`.
  * Always run `uv sync --dev` after editing `pyproject.toml`.

* **When generating documentation:**

  * Use Markdown.
  * Place docs in `docs/`.

## Example Tasks for Junie

* Suggest unit tests for new modules under `src/wolfie3d/`.
* Propose refactorings that reduce complexity while preserving behavior.
* Draft or improve documentation in `docs/`.
* Recommend dependency updates if newer stable versions exist.

---

**Note:** This file is intended to give Junie (and other AI coding assistants) clear project context and conventions, ensuring generated contributions align with the team’s standards.
