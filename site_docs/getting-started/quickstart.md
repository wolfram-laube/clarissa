# Quick Start

Get CLARISSA running in under 5 minutes.

## Prerequisites

- Python 3.10+
- pip

## Installation

```bash
# Clone the repository
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git
cd irena

# Install with development dependencies
pip install -e ".[dev]"
```

## Run the Demo

### Interactive Mode

```bash
python -m clarissa demo
```

This runs a minimal governed demo that:

1. Loads a mock reservoir deck
2. Proposes a rate change via the RL stub
3. Requests human approval (governance gate)
4. Runs the simulator
5. Explains the result

### CI Mode (Auto-Approve)

```bash
AUTO_APPROVE=1 python -m clarissa demo
```

## Run Tests

```bash
# All tests
pytest -q

# Contract tests only
pytest tests/contracts/ -v

# Snapshot tests only
pytest tests/golden/ -v
```

## Project Structure

```
src/clarissa/           # Main package
  ├── agent/            # Agent core
  ├── governance/       # Policy enforcement
  ├── learning/         # RL components (planned)
  └── simulators/       # Simulator adapters

src/clarissa_kernel/    # Native simulation kernel

tests/
  ├── contracts/        # Adapter contract tests
  └── golden/           # CLI snapshot tests
```

## Next Steps

- Read the [Architecture Overview](../architecture/overview.md)
- Explore the [ADRs](../architecture/adr/index.md)
- Check the [Contributing Guide](../development/contributing.md)
