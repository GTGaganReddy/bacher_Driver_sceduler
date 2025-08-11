#!/usr/bin/env python3
"""
Test script to verify Supabase database connection and retrieve data for July 7-13, 2025
"""
import os
import asyncpg
import asyncio
import json
from datetime import date

async def test_supabase_connection():
    """Test connection to Supabase and get data for July 7-13, 2025"""
    
    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    if not database_url:
        print("❌ No DATABASE_URL or SUPABASE_DATABASE_URL found")
        return
    
    print(f"🔗 Testing connection to Supabase database...")
    
    try:
        # Test connection
        conn = await asyncpg.connect(database_url)
        print("✅ Successfully connected to Supabase database")
        
        # Get drivers
        drivers = await conn.fetch("SELECT driver_id, name, monthly_hours_limit FROM drivers ORDER BY name")
        print(f"📋 Found {len(drivers)} drivers")
        
        # Get routes for July 7-13, 2025
        routes = await conn.fetch("""
            SELECT route_id, route_name, date, details 
            FROM routes 
            WHERE date >= '2025-07-07' AND date <= '2025-07-13'
            ORDER BY date, route_name
        """)
        print(f"🛣️  Found {len(routes)} routes for July 7-13, 2025")
        
        # Get availability data for this period
        availability = await conn.fetch("""
            SELECT driver_id, date, available 
            FROM driver_availability 
            WHERE date >= '2025-07-07' AND date <= '2025-07-13'
            ORDER BY date, driver_id
        """)
        print(f"📅 Found {len(availability)} availability records")
        
        # Show sample data
        if routes:
            print("\n📊 Sample route data:")
            for i, route in enumerate(routes[:5]):
                details = route['details'] if route['details'] else 'No details'
                print(f"  {route['date']} - {route['route_name']} - {details}")
            if len(routes) > 5:
                print(f"  ... and {len(routes) - 5} more routes")
        
        # Check if we have enough data for optimization
        unique_dates = set(str(route['date']) for route in routes)
        print(f"\n📆 Routes available for dates: {sorted(unique_dates)}")
        
        if len(drivers) >= 5 and len(routes) >= 10:
            print("✅ Sufficient data available for OR-Tools optimization")
            return True
        else:
            print("⚠️  Insufficient data for optimization")
            return False
            
        await conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_supabase_connection())