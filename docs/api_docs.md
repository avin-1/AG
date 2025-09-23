# FloatChat API Documentation

## Endpoints
- **POST /chat**: Submit a natural language query.
  - Input: `{ "text": "Show salinity profiles near the equator" }`
  - Output: `{ "response": "SQL query results" }`
- **GET /data**: Execute a raw SQL query (for debugging).

Access via `http://localhost:8000/docs` for Swagger UI.