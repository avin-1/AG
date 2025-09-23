conda activate ./venv
python src\data_ingestion\ingest_argo.py
python src\data_ingestion\metadata_extractor.py
python src\database\relational_db.py
python src\database\vector_db.py