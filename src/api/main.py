from fastapi import FastAPI
from src.api.routes import chat, data
from src.utils.logging import get_logger
from dotenv import load_dotenv

load_dotenv()  # load .env if present at project root

app = FastAPI(title="FloatChat API")
logger = get_logger(__name__)

app.include_router(chat.router, prefix="/api")
app.include_router(data.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)