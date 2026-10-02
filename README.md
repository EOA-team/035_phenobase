# Phenobase Dataplatform 

[![Python](https://img.shields.io/badge/python-3.12-blue)](.python-version)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPL%20v3-blue)](LICENSE)

Data platform for UAV Hyperspectral long-term experiments at Agroscope — standardizes data and pipelines, makes data queryable, and hides backend complexity so researchers focus on science instead
of wrestling with unorganized data, scripts, and models.


<img width="906" height="307" alt="image" src="https://github.com/user-attachments/assets/3e48367e-f584-40f8-80f0-de135cc26f4f" />

## Installation

```bash
git clone https://github.com/EOA-team/035_phenobase.git
conda env create -f environment.yml
conda activate 035_phenobase
```

## Project Structure
```
. 
├── src/              # source code
├── tests/            # tests
├── data/             # input data (excluded from git)
├── docs/             # cheatsheets, ...
├── results/          # outputs (excluded from git)
├── .github/workflows # CI configuration
├── environment.yml
└── README.md
```

## Run Local

**1. Install Docker Compose **
https://docs.docker.com/compose/install/

**2. Create PostgreSQL Container
```bash
cd docker
docker compose up -d
```
**3. Set your environemt in .env file**
```bash
cd docker
docker compose up -d
cd ..
```
**4. Run Tests (Independent of Agroscope Fola Infrastructure)**
```bash
pytest -s -v -m "not ags_fola"
```

**5. Start Phenobase **
```bash
uvicorn src.main:app --host localhost --port 8000
```
runs on http://localhost:8000/

**5. Start Mlflow **
```bash
mlflow server --host localhost --port 5000
```
runs on http://localhost:5000/

**6. Initialize Database with Test Users  **
```python
python -m src.scripts.database.00_reset
python -m src.scripts.database.01_load_users
python -m src.scripts.database.inspect_users
```
**7. Sample Upload (treatment)**
7.1 Go to  http://localhost:8000/docs
7.2 Use MAX_MUSTERMANN_API_KEY (Write Role)
7.3 Dowload csv template: 
http://localhost:8000/docs#/default/get_upload_template_data_upload_template__table_name__get
7.4 Upload adjusted csv file:
http://localhost:8000/docs#/default/upload_file_data_upload__table_name__post
7.6 Check if upload log is in STORAGE_LOCAL_PATH
7.7 Check if data is in database:
http://localhost:8000/docs#/default/get_table_data_data__table_name__get
