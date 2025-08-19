#!/usr/bin/env python3
"""
Standalone OR-Tools Optimizer Example
=====================================

This file contains the exact input/output format for the driver scheduling optimizer.
You can run this locally in VS Code to test your OR-Tools implementation.

Input Format: drivers, routes, availability (as they come from database)
Output Format: assignments structure that goes to Google Sheets service

To run: python optimizer_standalone_example.py
"""

import json
from typing import List, Dict
from datetime import datetime


def parse_time_string_to_hours(time_str: str) -> float:
    """Convert time string (HH:MM) to decimal hours"""
    if not time_str or not isinstance(time_str, str):
        return 8.0  # Default fallback
    
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours + (minutes / 60.0)
    except (ValueError, IndexError):
        pass
    
    return 8.0  # Default fallback


def parse_json_details(details_str: str) -> Dict:
    """Parse JSON string from database details field"""
    if not details_str:
        return {}
    
    try:
        return json.loads(details_str)
    except (json.JSONDecodeError, TypeError):
        return {}


# ==============================================================================
# INPUT FORMAT (as received from database APIs)
# ==============================================================================

# 1. DRIVERS INPUT FORMAT
sample_drivers = [
    {
        "driver_id": 1,
        "name": "Blaskovic, Nenad",
        "details": '{"monthly_hours": "160:00", "type": "regular"}',
        "created_at": "2025-08-11T20:17:18.748524"
    },
    {
        "driver_id": 2,
        "name": "Fröhlacher, Hubert", 
        "details": '{"monthly_hours": "160:00", "type": "regular"}',
        "created_at": "2025-08-11T20:17:18.748524"
    },
    {
        "driver_id": 21,
        "name": "Klagenfurt - Samstagsfahrer",
        "details": '{"monthly_hours": "40:00", "type": "saturday_only"}',
        "created_at": "2025-08-11T20:17:18.748524"
    }
    # ... 21 total drivers
]

# 2. ROUTES INPUT FORMAT
sample_routes = [
    {
        "route_id": 1,
        "date": "2025-07-07",
        "route_name": "431oS",
        "day_of_week": "monday",
        "details": '{"type": "weekday", "duration": "11:00", "route_code": "431oS"}'
    },
    {
        "route_id": 2,
        "date": "2025-07-07", 
        "route_name": "432oS",
        "day_of_week": "monday",
        "details": '{"type": "weekday", "duration": "12:00", "route_code": "432oS"}'
    },
    {
        "route_id": 42,
        "date": "2025-07-12",
        "route_name": "452SA", 
        "day_of_week": "saturday",
        "details": '{"type": "saturday", "duration": "10:00", "route_code": "452SA"}'
    }
    # ... 42 total routes across July 7-13, 2025
]

# 3. AVAILABILITY INPUT FORMAT  
sample_availability = [
    {
        "driver_id": 1,
        "date": "2025-07-07",
        "available": True
    },
    {
        "driver_id": 1,
        "date": "2025-07-13", 
        "available": False  # Sunday unavailable
    },
    {
        "driver_id": 21,
        "date": "2025-07-12",
        "available": True  # Saturday driver available on Saturday
    }
    # Default: All drivers available Monday-Saturday, unavailable Sunday
]


# ==============================================================================
# EXPECTED OUTPUT FORMAT (for Google Sheets service)
# ==============================================================================

expected_output_format = {
    "assignments": {
        "2025-07-07": {  # Date as string key
            "431oS": {  # Route name as key
                "driver_name": "Blaskovic, Nenad",
                "driver_id": 1,
                "route_id": 1,
                "duration_hours": 11.0,
                "duration_formatted": "11:00",
                "status": "assigned"  # CRITICAL: Must be "assigned" for sheets
            },
            "432oS": {
                "driver_name": "Fröhlacher, Hubert",
                "driver_id": 2,
                "route_id": 2,
                "duration_hours": 12.0,
                "duration_formatted": "12:00", 
                "status": "assigned"
            },
            # F entries for unavailable drivers (optional but system expects them)
            "F_SomeDriver_2025-07-07": {
                "driver_name": "SomeDriver",
                "driver_id": 99,
                "route_id": None,
                "duration_hours": 0.0,
                "duration_formatted": "00:00",
                "status": "unavailable"
            }
        },
        "2025-07-08": {
            # Similar structure for each date...
        },
        # ... continue for all dates 2025-07-07 through 2025-07-13
    },
    "unassigned_routes": [
        {
            "id": 42,
            "name": "someRoute",
            "date": "2025-07-07", 
            "duration_hours": 8.0
        }
        # Routes that couldn't be assigned
    ],
    "statistics": {
        "total_assignments": 42,
        "total_routes": 42,
        "unassigned_count": 0,
        "assignment_rate": 100.0,
        "objective_value": 0,
        "solve_time_ms": 0,
        "driver_utilization": {
            "1": {
                "driver_name": "Blaskovic, Nenad",
                "monthly_capacity_hours": 160.0,
                "available_days": 6,
                "hours_used": 44.0,
                "hours_remaining": 116.0,
                "utilization_rate": 0.275
            }
        },
        "special_assignment_452sa": "Successfully assigned"
    },
    "solver_status": "SEQUENTIAL_OPTIMAL"
}


# ==============================================================================
# YOUR OR-TOOLS IMPLEMENTATION GOES HERE
# ==============================================================================

def run_ortools_optimization(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict:
    """
    YOUR IMPLEMENTATION HERE
    
    Key Requirements:
    1. Use OR-Tools CP-SAT or Linear Programming solver
    2. Sequential day-by-day optimization (July 7-13, 2025)
    3. Constraints:
       - Each route assigned to at most one driver per day
       - Each driver can only have one route per day  
       - Driver remaining hours must not be exceeded
       - Special rule: Route "452SA" on Saturday must go to "Klagenfurt - Samstagsfahrer"
    4. Output format must match expected_output_format exactly
    5. Date keys must be strings in "YYYY-MM-DD" format
    6. All assignments must have status="assigned"
    
    Input Processing:
    - Parse driver details JSON for monthly_hours 
    - Parse route details JSON for duration
    - Build availability lookup by driver_id and date
    - Group routes by date for sequential solving
    
    Sequential Algorithm:
    - Sort dates chronologically (July 7, 8, 9, 10, 11, 12) 
    - For each date, create fresh solver instance
    - Track remaining driver hours across dates
    - Assign routes, then reduce remaining hours for next date
    """
    
    # YOUR OR-TOOLS CODE HERE
    # Replace this placeholder with your actual implementation
    
    return {
        "assignments": {},
        "unassigned_routes": [],
        "statistics": {"total_assignments": 0},
        "solver_status": "NOT_IMPLEMENTED"
    }


# ==============================================================================
# TEST RUNNER
# ==============================================================================

def main():
    """Test the optimizer with sample data"""
    print("=" * 60)
    print("OR-Tools Driver Scheduling Optimizer Test")
    print("=" * 60)
    
    print(f"\nInput Summary:")
    print(f"- Drivers: {len(sample_drivers)}")
    print(f"- Routes: {len(sample_routes)}")  
    print(f"- Availability entries: {len(sample_availability)}")
    
    print(f"\nSample Driver:")
    print(json.dumps(sample_drivers[0], indent=2))
    
    print(f"\nSample Route:")
    print(json.dumps(sample_routes[0], indent=2))
    
    print(f"\nSample Availability:")
    print(json.dumps(sample_availability[0], indent=2))
    
    print(f"\n" + "=" * 40)
    print("Running optimization...")
    print("=" * 40)
    
    result = run_ortools_optimization(sample_drivers, sample_routes, sample_availability)
    
    print(f"\nOptimization Result:")
    print(f"- Status: {result.get('solver_status', 'UNKNOWN')}")
    print(f"- Total assignments: {result.get('statistics', {}).get('total_assignments', 0)}")
    print(f"- Assignment dates: {list(result.get('assignments', {}).keys())}")
    
    print(f"\nFull result structure:")
    print(json.dumps(result, indent=2))
    
    print(f"\n" + "=" * 60)
    print("Expected Output Format (for reference):")
    print("=" * 60)
    print(json.dumps(expected_output_format, indent=2))


if __name__ == "__main__":
    main()