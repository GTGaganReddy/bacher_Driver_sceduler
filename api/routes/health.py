from fastapi import APIRouter, Depends
from database.connection import DatabaseManager
from schemas.models import SuccessResponse

router = APIRouter()

@router.get("/health", response_model=SuccessResponse)
async def health_check():
    """Health check endpoint"""
    return SuccessResponse(
        status="success",
        message="Service is healthy",
        data={"service": "Driver Scheduling Backend", "status": "operational"}
    )

@router.get("/health/db", response_model=SuccessResponse)
async def database_health():
    """Database health check endpoint - initializes database if needed for deployment"""
    try:
        # Import here to avoid circular imports
        from api.dependencies import db_manager
        
        # Initialize database pool if not already done (for deployment environments)
        if not db_manager.pool:
            try:
                await db_manager.init_pool()
            except Exception as init_error:
                return SuccessResponse(
                    status="error",
                    message=f"Failed to initialize database pool: {str(init_error)}"
                )
        
        # Test database connection
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            
        if result == 1:
            return SuccessResponse(
                status="success",
                message="Database is healthy",
                data={"database": "operational", "connection": "active"}
            )
        else:
            return SuccessResponse(
                status="error",
                message="Database health check failed"
            )
    except Exception as e:
        return SuccessResponse(
            status="error",
            message=f"Database error: {str(e)}"
        )
