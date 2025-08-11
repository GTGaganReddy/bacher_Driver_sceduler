#!/usr/bin/env python3
"""
Debug script to show exact data formats from database vs OR-Tools input
"""
import asyncio
import json
from datetime import date
from services.database import DatabaseService
from config.settings import Settings

async def debug_data_formats():
    print("=== DATABASE OUTPUT FORMAT ===")
    
    settings = Settings()
    db_service = DatabaseService(settings)
    
    # Get actual database data
    week_start = date(2025, 7, 7)
    week_end = date(2025, 7, 13)
    
    drivers = await db_service.get_drivers()
    routes = await db_service.get_routes_by_date_range(week_start, week_end)
    availability = await db_service.get_availability_by_date_range(week_start, week_end)
    
    print(f"\n1. DRIVERS FROM DATABASE ({len(drivers)} records):")
    print("Sample driver record:")
    if drivers:
        sample_driver = drivers[0]
        print(json.dumps(dict(sample_driver), indent=2, default=str))
    
    print(f"\n2. ROUTES FROM DATABASE ({len(routes)} records):")
    print("Sample route record:")
    if routes:
        sample_route = routes[0]
        print(json.dumps(dict(sample_route), indent=2, default=str))
    
    print(f"\n3. AVAILABILITY FROM DATABASE ({len(availability)} records):")
    print("Sample availability record:")
    if availability:
        sample_availability = availability[0]
        print(json.dumps(dict(sample_availability), indent=2, default=str))
    
    print("\n=== OR-TOOLS EXPECTED INPUT FORMAT ===")
    
    print("\n1. OR-Tools expects DRIVERS as:")
    print("""[
    {
        "driver_id": 1,
        "name": "Driver Name",
        "monthly_hours_limit": 174,
        "details": {"type": "full_time", "monthly_hours": "174:00"}  # Optional
    }
]""")
    
    print("\n2. OR-Tools expects ROUTES as:")
    print("""[
    {
        "route_id": 1,
        "date": "2025-07-07" or date(2025, 7, 7),
        "route_name": "431oS",
        "details": {"duration": "11:00", "type": "weekday"}  # JSON string or dict
    }
]""")
    
    print("\n3. OR-Tools expects AVAILABILITY as:")
    print("""[
    {
        "driver_id": 1,
        "date": "2025-07-07" or date(2025, 7, 7),
        "available": True,
        "available_hours": 8.0 or Decimal('8.00'),
        "max_routes": 2,
        "shift_preference": "any"
    }
]""")
    
    print("\n=== CONVERSION ISSUES IDENTIFIED ===")
    print("1. Database 'details' fields are JSON strings, OR-Tools expects parsed dicts")
    print("2. Database uses Decimal types, OR-Tools expects float")
    print("3. Database has extra fields (id, created_at, etc.) that OR-Tools ignores")
    print("4. Route duration parsing: '11:00' -> 11.0 hours (float conversion)")
    
    await db_service.close()

if __name__ == "__main__":
    asyncio.run(debug_data_formats())