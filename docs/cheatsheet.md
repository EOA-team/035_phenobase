### Conda
```bash
conda env create -f environment.yml   # create env from spec file
conda env list                        # list all environments
conda activate 035_phenobase          # activate env by name
conda env update -f environment.yml --prune   # sync live env to spec file (removes old pkgs)
```

### Mypy

```bash
mypy .              # Static type checking
```

### Ruff

```bash
ruff check          # Show linting errors (lint + complexity + security)
ruff check --diff   # Preview what --fix would change
ruff check --fix    # Auto-fix what it can

ruff format         # Auto-format
ruff format --check # Check formatting, show what would change
ruff format --diff  # Preview formatting diff
```

### Pytest

```bash
pytest --cov=src/ --cov-fail-under=80  # Check coverage
pytest -s -v                           # Run all tests 
```