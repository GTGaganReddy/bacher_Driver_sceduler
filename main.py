from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.settings import settings
from api.routes import drivers, routes, scheduling, health
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Driver Scheduling Backend...")
    from api.dependencies import db_manager
    await db_manager.init_pool()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await db_manager.close_pool()

# Create FastAPI application
app = FastAPI(
    title="Driver Scheduling Backend",
    description="Backend service for logistics driver scheduling with OR-Tools optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(drivers.router, prefix="/api/v1", tags=["Drivers"])
app.include_router(routes.router, prefix="/api/v1", tags=["Routes"])
app.include_router(scheduling.router, prefix="/api/v1", tags=["Scheduling"])

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "Driver Scheduling Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=settings.DEBUG)
