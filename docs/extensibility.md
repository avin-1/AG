# Extensibility Notes

## Adding New Data Sources
- Create new ingestion scripts in `src/data_ingestion/`.
- Update `relational_db.py` for new schemas.
- Extend `metadata_extractor.py` for new metadata.

## Supporting New Queries
- Update `query_translator.py` with new rules.
- Enhance RAG prompts in `rag_pipeline.py`.

## Future Data
- BGC/glider: Extend ingestion to handle new NetCDF formats.
- Satellite: Add API calls to fetch satellite data.