from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date
from services.database import DatabaseService
from schemas.models import Route, RouteCreate, RouteUpdate, SuccessResponse
from api.dependencies import get_database_service

router = APIRouter()

@router.get("/routes", response_model=List[Route])
async def get_routes(
    start_date: date,
    end_date: date,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get routes within a date range"""
    try:
        routes = await db_service.get_routes_by_date_range(start_date, end_date)
        return routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch routes: {str(e)}")

@router.post("/routes", response_model=SuccessResponse)
async def create_route(
    route: RouteCreate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Create a new route"""
    try:
        route_id = await db_service.create_route(
            route.date,
            route.route_name,
            route.details
        )
        return SuccessResponse(
            status="success",
            message="Route created successfully",
            data={"route_id": route_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create route: {str(e)}")

@router.put("/routes/{route_id}", response_model=SuccessResponse)
async def update_route(
    route_id: int,
    route: RouteUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Update an existing route"""
    try:
        await db_service.update_route(
            route_id,
            route.date,
            route.route_name,
            route.details
        )
        return SuccessResponse(
            status="success",
            message="Route updated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update route: {str(e)}")

@router.delete("/routes/{route_id}", response_model=SuccessResponse)
async def delete_route(
    route_id: int,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Delete a route"""
    try:
        await db_service.delete_route(route_id)
        return SuccessResponse(
            status="success",
            message="Route deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete route: {str(e)}")
