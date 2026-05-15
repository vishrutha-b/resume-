from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routes.api import router as api_router
from routes.auth import router as auth_router
from routes.web import router as web_router
from models.database import init_db, close_db
from config.settings import Config
import os
from utils.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    init_db()
    logger.info(f"Connected to MongoDB at {Config.MONGO_URI}")
    yield
    # Shutdown
    logger.info("Shutting down...")
    close_db()

app = FastAPI(
    title="Aura ATS API",
    description="Resume screening and optimization API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(web_router, tags=["Web UI"])
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
