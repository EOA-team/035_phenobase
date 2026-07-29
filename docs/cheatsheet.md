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
# Run all (unit-tests)(integration-tests)(slow integration-tests)
pytest -s -v           
pytest --cov=src/ --cov-fail-under=80

# Run only (unit-tests)(integration-tests)
pytest -s -v \
--without-slow-integration       

pytest --cov=src/ --cov-fail-under=80 \
 --without-slow-integration 

# Run only (unit-tests)
pytest -s -v \
--without-slow-integration \
--without-integration

pytest --cov=src/ --cov-fail-under=80 \
--without-slow-integration \
--without-integration

```

### start traefik(powershell)

```bash
& "C:\Traefik\traefik.exe" --configFile="C:\Traefik\traefik.yml"  
```
### uvicorn 
```bash
uvicorn src.scripts.api_dummy:app --host localhost --port 8000
```

### mlflow 
```bash
mlflow server --host localhost --port 5000 --allowed-hosts "mlflow.phenobase.agsad.admin.ch" 
```