# Contributing

## ADR Discipline

If a change alters behavior, responsibilities, authority, or safety boundaries, it should:

- Reference an existing ADR, or
- Introduce a new ADR in `docs/adr/`

## Code Boundaries

```
src/clarissa/     ←── importable package
experiments/      ←── may import clarissa
```

!!! warning "Import Rule"
    `src/clarissa/` must **never** import from `experiments/`.

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

Follow existing patterns. Update tests if behavior changes.

### 3. Run Tests

```bash
# All tests
pytest -q

# With coverage
pytest --cov=clarissa
```

### 4. Update Snapshots (if CLI changed)

```bash
make update-snapshots
```

### 5. Commit

```bash
git add .
git commit -m "feat: add my feature"
```

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code restructure
- `test:` - Test changes
- `chore:` - Maintenance

### 6. Push & Create MR

```bash
git push -u origin feature/my-feature
```

Create Merge Request in GitLab.

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Hooks run:

- CLI snapshot tests
- Fast smoke tests

## Testing Guidelines

### Contract Tests

For simulator adapters, add tests in `tests/contracts/`:

```python
@pytest.mark.parametrize("name,sim", adapters())
def test_simulator_run_contract(name, sim):
    out = sim.run("WELL A RATE 90")
    assert "converged" in out
    assert isinstance(out["errors"], list)
```

### Snapshot Tests

For CLI output stability, tests are in `tests/golden/`.

Update snapshots with:

```bash
make update-snapshots
```

## Documentation

- Update relevant docs when adding features
- ADRs live in `docs/adr/`
- Run `mkdocs serve` locally to preview

## Questions?

Open an issue or reach out to the maintainers.
