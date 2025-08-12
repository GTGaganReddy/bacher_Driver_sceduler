from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.settings import settings
from api.routes import drivers, routes, scheduling, health, assistant_api
import logging
import os

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
app.include_router(assistant_api.router, tags=["Assistant API"])
# app.include_router(supabase_ops.router, prefix="/api/v1", tags=["Supabase Operations"])

@app.get("/")
async def root():
    """Root endpoint with API info - serves as a quick health check for deployment"""
    try:
        # Quick database connectivity check for deployment health
        from api.dependencies import db_manager
        if db_manager.pool is not None:
            db_status = "connected"
        else:
            db_status = "not_connected"
        
        return {
            "service": "Driver Scheduling Backend",
            "version": "1.0.0",
            "status": "healthy",
            "database": db_status,
            "docs": "/docs",
            "health": "/health",
            "rapid_health": "/healthz"
        }
    except Exception as e:
        logger.warning(f"Root endpoint health check warning: {str(e)}")
        # Still return healthy status for deployment, but log the warning
        return {
            "service": "Driver Scheduling Backend",
            "version": "1.0.0",
            "status": "healthy",
            "database": "unknown",
            "docs": "/docs",
            "health": "/health",
            "rapid_health": "/healthz"
        }

@app.get("/healthz")
async def rapid_health_check():
    """Rapid health check endpoint for deployment health checks - always responds quickly"""
    return {"status": "ok", "timestamp": "deployment-ready"}

@app.get("/ready")
async def readiness_check():
    """Kubernetes/Cloud Run readiness check endpoint"""
    return {"status": "ready", "service": "driver-scheduling-backend"}

@app.get("/live") 
async def liveness_check():
    """Kubernetes/Cloud Run liveness check endpoint"""
    return {"status": "alive", "service": "driver-scheduling-backend"}

if __name__ == "__main__":
    import uvicorn
    # Always use PORT environment variable for deployment (Cloud Run sets this)
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting FastAPI server on host 0.0.0.0 port {port}")
    logger.info(f"Environment: {'DEPLOYMENT' if settings.IS_DEPLOYMENT else 'DEVELOPMENT'}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Disable reload in production for deployment stability
    reload = settings.DEBUG and not settings.IS_DEPLOYMENT
    
    # Production-optimized uvicorn configuration
    uvicorn_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": port,
        "reload": reload
    }
    
    # Additional production settings for deployment
    if settings.IS_DEPLOYMENT:
        uvicorn_config.update({
            "workers": 1,  # Single worker for Cloud Run
            "log_level": "info",
            "access_log": True,
            "use_colors": False  # Better for deployment logs
        })
        logger.info("Production configuration applied for deployment")
    
    uvicorn.run(**uvicorn_config)
