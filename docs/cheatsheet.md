### Conda
```bash
conda env create -f environment.yml   # create env from spec file
conda env list                        # list all environments
conda activate 035_phenobase          # activate env by name
conda env update -f environment.yml --prune   # sync live env to spec file (removes old pkgs)
```

### Autopep9

```bash
autopep8 --in-place file.py  # Apply directly on file
autopep8 --diff file.py      # Check what would change first  

```

### Pytest

```bash
pytest --cov=src/ --cov-fail-under=80 # Check coverage
pytest -s -v # Run all Tests 
```