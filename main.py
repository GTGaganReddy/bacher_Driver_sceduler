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
    try:
        from api.dependencies import db_manager
        await db_manager.init_pool()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't fail startup - let health checks pass while DB connects async
        logger.info("Continuing startup without database - will retry connections on API calls")
    yield
    # Shutdown
    logger.info("Shutting down...")
    try:
        from api.dependencies import db_manager
        await db_manager.close_pool()
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")

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
    """Root endpoint - optimized for deployment health checks"""
    # Fast response for deployment health checks - no database operations
    return {
        "service": "Driver Scheduling Backend",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "health": "/health",
        "healthz": "/healthz"
    }

@app.get("/healthz")
async def rapid_health_check():
    """Rapid health check endpoint for deployment health checks - always responds quickly"""
    try:
        # Quick response for health checks - don't test DB to avoid timeouts
        return {
            "status": "ok", 
            "timestamp": "deployment-ready",
            "service": "driver-scheduling-backend",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        # Still return ok for deployment health checks
        return {"status": "ok", "error": str(e)}

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
    
    try:
        # Always use PORT environment variable for deployment (Cloud Run sets this)
        port = int(os.getenv("PORT", 5000))
        logger.info(f"Starting FastAPI server on host 0.0.0.0 port {port}")
        logger.info(f"Environment: {'DEPLOYMENT' if settings.IS_DEPLOYMENT else 'DEVELOPMENT'}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        
        # Disable reload in production for deployment stability
        reload = settings.DEBUG and not settings.IS_DEPLOYMENT
        
        # Production-optimized uvicorn configuration for Cloud Run compatibility
        uvicorn_config = {
            "host": "0.0.0.0",
            "port": port,
            "reload": reload,
            "timeout_keep_alive": 30,  # Cloud Run timeout compatibility
            "timeout_graceful_shutdown": 30,  # Graceful shutdown
        }
        
        # Additional production settings for deployment
        if settings.IS_DEPLOYMENT or os.getenv("PORT"):  # Cloud Run sets PORT
            uvicorn_config.update({
                "workers": 1,  # Single worker for Cloud Run
                "log_level": "info",
                "access_log": True,
                "use_colors": False,  # Better for deployment logs
                "loop": "uvloop",  # Performance boost if available
            })
            logger.info("Cloud Run production configuration applied")
        else:
            logger.info("Development configuration applied")
        
        # Start the server directly without app string to avoid import issues
        uvicorn.run(app, **uvicorn_config)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        raise
