# Installation

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| pip | Latest |

## Standard Installation

```bash
# Clone
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
cd irena

# Install in editable mode
pip install -e .
```

## Development Installation

```bash
# Install with dev dependencies (pytest, ruff)
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check CLI
python -m clarissa --help

# Run tests
pytest -q
```

## Optional: Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

This enables:

- CLI snapshot validation on commit
- Fast smoke tests

## Air-Gapped Installation

For environments without internet access:

1. On a connected machine, download dependencies:
   ```bash
   pip download -d ./wheels -e ".[dev]"
   ```

2. Transfer the `wheels/` directory and source code

3. On the air-gapped machine:
   ```bash
   pip install --no-index --find-links=./wheels -e ".[dev]"
   ```

## Troubleshooting

### ModuleNotFoundError: clarissa

Ensure you installed in editable mode (`-e` flag):

```bash
pip install -e .
```

### Tests fail with import errors

Make sure you're in the repository root and have installed dev dependencies:

```bash
pip install -e ".[dev]"
```
