# Phenobase Dataplatform 

[![Python](https://img.shields.io/badge/python-3.12-blue)](.python-version)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL%20v3-blue)](LICENSE)

Data platform for UAV Hyperspectral long-term experiments at Agroscope — standardizes data and pipelines, makes data queryable, and hides backend complexity so researchers focus on science instead
of wrestling with unorganized data, scripts, and models.


<img width="906" height="307" alt="image" src="https://github.com/user-attachments/assets/3e48367e-f584-40f8-80f0-de135cc26f4f" />

## Installation

```bash
git clone git@github.com:EOA-team/035_phenobase.git
conda env create -f environment.yml
conda activate 035_phenobase_py312
```

## Project Structure
```
. 
├── src/              # source code
├── tests/            # tests
├── data/             # input data (excluded from git)
├── results/          # outputs (excluded from git)
├── .github/workflows # CI configuration
├── environment.yml
└── README.md
```
