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

app = FastAPI(
    title="Aura ATS API",
    description="Resume screening and optimization API",
    version="2.0.0"
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

# Startup and Shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application...")
    init_db()
    logger.info(f"Connected to MongoDB at {Config.MONGO_URI}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    close_db()

# Include routers
app.include_router(web_router, tags=["Web UI"])
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=Config.DEBUG)
