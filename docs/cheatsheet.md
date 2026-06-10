### Conda
```bash
conda env create -f environment.yml   # create env from spec file
conda env list                        # list all environments
conda activate 035_phenobase          # activate env by name
conda env update -f environment.yml --prune   # sync live env to spec file (removes old pkgs)
```