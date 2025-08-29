# Wolfie3D

Pygame-based 3D shooter prototype (currently scaffolding and tooling). This repo uses the `uv` Python package/dependency manager for fast, reproducible environments.


## Quick Start

Prerequisites:
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed (`pipx install uv` or see uv docs)

Setup dependencies (including dev tools):

```bash
uv sync --dev
```

Run the game:

```bash
uv run python -m wolfie3d
```

If you prefer a simpler variant without enemies (for debugging/demo):

```bash
uv run python -m wolfie3d.game_no_enemies
```

> Tip: `uv run` executes commands inside the project’s virtual environment without activating it manually.


## Development Workflow

Common checks:

```bash
uv run python -m ruff check .
uv run python -m mypy src
uv run python -m pytest
```

Format code:

```bash
uv run python -m black .
```

Coverage:

```bash
PYTHONPATH=src uv run python -m pytest --cov --cov-report=term-missing
```

Pre-commit (optional, if you enable hooks):

```bash
uv run python -m pre_commit run --all-files || uv run python -m pre-commit run --all-files
```


## Project Structure

- `src/wolfie3d/` — core package (entry point: `python -m wolfie3d`)
- `assets/` — game assets (textures, sprites, etc.)
- `tests/` — unit/integration tests (add new ones here)
- `docs/` — design notes and documentation
- `scripts/` — helper scripts


## Running Without uv (not recommended)

You can still use a traditional virtualenv, but we recommend `uv` for speed and reproducibility.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
python -m wolfie3d
```


## Troubleshooting

- Import errors or missing packages: run `uv sync --dev` again.
- Pygame display issues on headless machines/CI: use a virtual framebuffer or skip running the game; tests shouldn’t require a display by default.
- If `uv` is not found, install it via `pipx install uv` or see the official docs linked above.


## Contributing

- Follow Black/Ruff/Mypy rules; keep functions small and documented.
- All new code in `src/` should have corresponding tests in `tests/`.
- Use conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
- Open PRs from `feat/*`, `fix/*`, etc. branches; ensure checks pass before review.


## License

TBD.
