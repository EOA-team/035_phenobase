### Conda
```bash
conda env create -f environment.yml   # create env from spec file
conda env list                        # list all environments
conda activate 035_phenobase          # activate env by name
conda env update -f environment.yml --prune   # sync live env to spec file (removes old pkgs)
```

### Mypy

```bash
mypy src/                              # Static type checking
```

### Ruff

```bash
ruff check src/ tests/                 # Show linting errors (lint + complexity + security)
ruff check --diff src/ tests/          # Preview what --fix would change
ruff check --fix src/ tests/           # Auto-fix what it can
ruff format --check src/ tests/        # Check formatting, show what would change
ruff format --diff src/ tests/         # Preview formatting diff
ruff format src/ tests/                # Auto-format
```

### Conda-audit

```bash
conda-audit -n 035_phenobase           # Scan conda env for known CVEs
```

### Pytest

```bash
pytest --cov=src/ --cov-fail-under=80  # Check coverage
pytest -s -v                           # Run all tests 
```