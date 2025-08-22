"""
Cloudflare Workers compatible FastAPI application
Direct copy of main.py with Cloudflare-specific configurations
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Driver Scheduling Backend on Cloudflare Workers...")
    try:
        # Import dependencies here to avoid circular imports
        from api.dependencies import db_manager
        await db_manager.init_pool()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.info("Continuing startup without database - will retry connections on API calls")
    yield
    # Shutdown
    logger.info("Shutting down...")
    try:
        from api.dependencies import db_manager
        await db_manager.close_pool()
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")

# Create FastAPI app with custom domain support
app = FastAPI(
    title="Driver Scheduling API",
    description="Advanced driver route optimization and scheduling system with OR-Tools",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for custom domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.yourdomain.com",  # Replace with your actual domain
        "https://yourdomain.com",
        "http://localhost:3000",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers for production
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Powered-By"] = "Cloudflare Workers"
    response.headers["X-API-Version"] = "1.0.0"
    
    return response

# Import and register routers
from api.routes import drivers, routes, scheduling, assistant_api

app.include_router(drivers.router, prefix="/api/v1", tags=["Drivers"])
app.include_router(routes.router, prefix="/api/v1", tags=["Routes"])
app.include_router(scheduling.router, prefix="/api/v1", tags=["Scheduling"])
app.include_router(assistant_api.router, tags=["Assistant API"])

@app.get("/")
async def root():
    """Root endpoint - optimized for deployment health checks"""
    return {
        "service": "Driver Scheduling Backend",
        "version": "1.0.0", 
        "status": "healthy",
        "platform": "Cloudflare Workers",
        "docs": "/docs",
        "health": "/health",
        "healthz": "/healthz"
    }

@app.get("/healthz")
async def health_check():
    """Fast health check for deployment"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
async def detailed_health():
    """Detailed health check with database status"""
    try:
        from api.dependencies import db_manager
        if db_manager.pool is not None:
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "Cloudflare Workers"
        }
    except Exception as e:
        logger.warning(f"Health check database error: {e}")
        return {
            "status": "degraded",
            "database": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "Cloudflare Workers"
        }

@app.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness check"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

@app.get("/live")
async def liveness_check():
    """Kubernetes-style liveness check"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url)}
    )