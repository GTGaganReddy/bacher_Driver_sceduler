#!/usr/bin/env python3
"""
Test script to verify fixed assignments are being fetched correctly
"""

import asyncio
import sys
import logging
from services.database import DatabaseService
from api.dependencies import db_manager
from datetime import datetime

async def test_fixed_assignments():
    """Test fetching fixed assignments from database"""
    try:
        # Initialize database
        await db_manager.init_pool()
        
        # Create database service
        db_service = DatabaseService(db_manager)
        
        # Test date range for July 7-13, 2025
        week_start = datetime.strptime('2025-07-07', '%Y-%m-%d').date()
        week_end = datetime.strptime('2025-07-13', '%Y-%m-%d').date()
        
        print(f"Testing fixed assignments fetch for {week_start} to {week_end}")
        
        # Test raw SQL query first  
        async with db_manager.get_connection() as conn:
            raw_rows = await conn.fetch("""
                SELECT fa.*, d.name as driver_name, r.route_name
                FROM fixed_assignments fa
                JOIN drivers d ON fa.driver_id = d.driver_id
                JOIN routes r ON fa.route_id = r.route_id
                WHERE fa.date BETWEEN $1 AND $2
                ORDER BY fa.date, fa.driver_id
            """, week_start, week_end)
            print(f"Raw SQL query returned {len(raw_rows)} rows")
            
        # Now test the database service method
        fixed_assignments = await db_service.get_fixed_assignments_by_date_range(week_start, week_end)
        
        print(f"Database service method returned {len(fixed_assignments)} fixed assignments")
        
        if fixed_assignments:
            print("Sample fixed assignments:")
            for i, assignment in enumerate(fixed_assignments[:5]):  # Show first 5
                print(f"  {i+1}. Route {assignment['route_id']} ({assignment.get('route_name', 'N/A')}) on {assignment['date']} -> Driver {assignment['driver_id']} ({assignment.get('driver_name', 'N/A')})")
        else:
            print("No fixed assignments found!")
            
        # Close database connection
        await db_manager.close_pool()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the test
    asyncio.run(test_fixed_assignments())