"""
OpenAI Assistant Action Code for Driver Scheduling System

This code provides complete integration with the Driver Scheduling Backend API.
It supports all four main operations:
1. System Status Check
2. Weekly Optimization
3. Update Driver Availability (with F entry support)
4. Add New Routes
5. System Reset

Usage Instructions:
1. Replace YOUR_API_BASE_URL with your actual FastAPI server URL
2. Use this code as an OpenAI Assistant action
3. The Assistant can now manage driver scheduling through natural language
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class DriverSchedulingClient:
    """Client for Driver Scheduling Backend API"""
    
    def __init__(self, base_url: str = "YOUR_API_BASE_URL"):
        self.base_url = base_url.rstrip('/')
        self.headers = {"Content-Type": "application/json"}
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Check system status and health"""
        return self._make_request("GET", "/api/v1/assistant/status")
    
    def reset_system(self) -> Dict[str, Any]:
        """Reset system to initial state - clear assignments and reset availability"""
        return self._make_request("POST", "/api/v1/assistant/reset")
    
    def optimize_week(self, week_start: str) -> Dict[str, Any]:
        """Run complete weekly optimization for specified week"""
        data = {"week_start": week_start}
        return self._make_request("POST", "/api/v1/assistant/optimize-week", data)
    
    def update_driver_availability(self, driver_name: str, availability_updates: List[Dict], week_start: str) -> Dict[str, Any]:
        """Update driver availability and rerun optimization"""
        data = {
            "driver_name": driver_name,
            "updates": availability_updates,
            "week_start": week_start
        }
        return self._make_request("POST", "/api/v1/assistant/update-availability", data)
    
    def update_single_driver_availability(self, driver_name: str, date: str, available: bool) -> Dict[str, Any]:
        """Simplified method to update single driver availability"""
        data = {
            "driver_name": driver_name,
            "date": date,
            "available": available
        }
        return self._make_request("POST", "/api/v1/assistant/update-driver-availability", data)
    
    def add_route(self, route_name: str, date: str, duration_hours: float, 
                  day_of_week: str, week_start: str, route_type: str = "regular") -> Dict[str, Any]:
        """Add new route and rerun optimization"""
        data = {
            "route_name": route_name,
            "date": date,
            "duration_hours": duration_hours,
            "route_type": route_type,
            "day_of_week": day_of_week,
            "week_start": week_start
        }
        return self._make_request("POST", "/api/v1/assistant/add-route", data)


def get_july_week_2025():
    """Helper to get July 7-13, 2025 week dates"""
    return "2025-07-07"


# OpenAI Assistant Action Functions
def check_system_status():
    """Check the health and status of the driver scheduling system"""
    client = DriverSchedulingClient()
    result = client.get_system_status()
    
    if "error" in result:
        return f"❌ System Status Error: {result['error']}"
    
    if result.get("status") == "operational":
        return f"""✅ Driver Scheduling System Status: OPERATIONAL
        
📊 System Information:
• Drivers: {result.get('drivers_count', 'Unknown')} active drivers
• OR-Tools Optimization: {'✅ Enabled' if result.get('or_tools_enabled') else '❌ Disabled'}
• Google Sheets Integration: {'✅ Connected' if result.get('google_sheets_integration') else '❌ Disconnected'}

The system is ready for scheduling operations."""
    
    return f"⚠️ System Status: {result.get('status', 'Unknown')} - {result.get('message', '')}"


def reset_scheduling_system():
    """Reset the entire scheduling system to initial state"""
    client = DriverSchedulingClient()
    result = client.reset_system()
    
    if "error" in result:
        return f"❌ Reset Failed: {result['error']}"
    
    if result.get("status") == "success":
        return f"""🔄 System Reset Completed Successfully!
        
📊 Reset Summary:
• {result.get('drivers_count', 0)} drivers restored to available status
• {result.get('routes_count', 0)} routes ready for assignment
• All previous assignments cleared
• Driver availability reset (weekdays: available, Sunday: unavailable)
• System ready for fresh optimization

The system has been reset to its initial state and is ready for new scheduling."""
    
    return f"❌ Reset failed: {result.get('message', 'Unknown error')}"


def run_weekly_optimization(week_start: str = None):
    """Run complete weekly optimization for July 7-13, 2025"""
    if not week_start:
        week_start = get_july_week_2025()
    
    client = DriverSchedulingClient()
    result = client.optimize_week(week_start)
    
    if "error" in result:
        return f"❌ Optimization Failed: {result['error']}"
    
    if result.get("status") == "success":
        return f"""✅ Weekly Optimization Completed Successfully!
        
📊 Optimization Results:
• Week: {result.get('week_start')} to {(datetime.strptime(result.get('week_start'), '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')}
• Total Assignments: {result.get('total_assignments', 0)} route assignments created
• Total Routes: {result.get('total_routes', 0)} routes processed
• Google Sheets: {'✅ Updated' if result.get('google_sheets_updated') else '❌ Update Failed'}
• Solver Status: {result.get('solver_status', 'N/A')}

All driver-route assignments have been optimized and exported to Google Sheets."""
    
    return f"❌ Optimization failed: {result.get('message', 'Unknown error')}"


def update_driver_availability(driver_name: str, date: str, available: bool):
    """Update a driver's availability for a specific date"""
    client = DriverSchedulingClient()
    result = client.update_single_driver_availability(driver_name, date, available)
    
    if "error" in result:
        return f"❌ Availability Update Failed: {result['error']}"
    
    if result.get("status") == "success":
        status_text = "available" if available else "unavailable (F entry will be created)"
        return f"""✅ Driver Availability Updated Successfully!
        
📊 Update Results:
• Driver: {result.get('driver_updated')} 
• Date: {date}
• Status: {status_text}
• Updates Applied: {result.get('updates_applied', 0)}
• New Total Assignments: {result.get('total_assignments', 0)}
• Google Sheets: {'✅ Updated' if result.get('google_sheets_updated') else '❌ Update Failed'}

The system has been reoptimized with the new availability and results exported to Google Sheets."""
    
    return f"❌ Availability update failed: Driver not found or invalid data"


def add_new_route(route_name: str, date: str, duration_hours: float, day_of_week: str = None):
    """Add a new route to the system and reoptimize"""
    week_start = get_july_week_2025()
    
    # Auto-determine day of week if not provided
    if not day_of_week:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_of_week = date_obj.strftime('%A').lower()
    
    client = DriverSchedulingClient()
    result = client.add_route(route_name, date, duration_hours, day_of_week, week_start)
    
    if "error" in result:
        return f"❌ Route Addition Failed: {result['error']}"
    
    if result.get("status") == "success":
        route_info = result.get('route_added', {})
        return f"""✅ Route Added Successfully!
        
📊 New Route Details:
• Route Name: {route_info.get('name', route_name)}
• Date: {route_info.get('date', date)}
• Duration: {route_info.get('duration_hours', duration_hours)} hours
• Day: {day_of_week.title()}
• Route ID: {route_info.get('id', 'N/A')}

📊 System Update Results:
• Total Assignments: {result.get('total_assignments', 0)} (including new route)
• Total Routes: {result.get('total_routes', 0)} routes in system
• Google Sheets: {'✅ Updated' if result.get('google_sheets_updated') else '❌ Update Failed'}

The new route has been added and the system reoptimized with updated assignments."""
    
    return f"❌ Route addition failed: Invalid route data or system error"


# Example OpenAI Assistant Integration Functions
def handle_scheduling_request(action: str, **kwargs) -> str:
    """
    Main handler for OpenAI Assistant scheduling requests
    
    Actions supported:
    - "status": Check system health
    - "reset": Reset system to initial state  
    - "optimize": Run weekly optimization
    - "update_availability": Update driver availability
    - "add_route": Add new route
    """
    
    action = action.lower().strip()
    
    if action == "status":
        return check_system_status()
    
    elif action == "reset":
        return reset_scheduling_system()
    
    elif action == "optimize":
        week_start = kwargs.get("week_start")
        return run_weekly_optimization(week_start)
    
    elif action == "update_availability":
        driver_name = kwargs.get("driver_name", "")
        date = kwargs.get("date", "")
        available = kwargs.get("available", True)
        
        if not driver_name or not date:
            return "❌ Error: driver_name and date are required for availability updates"
        
        return update_driver_availability(driver_name, date, available)
    
    elif action == "add_route":
        route_name = kwargs.get("route_name", "")
        date = kwargs.get("date", "")
        duration_hours = kwargs.get("duration_hours", 0)
        day_of_week = kwargs.get("day_of_week")
        
        if not route_name or not date or duration_hours <= 0:
            return "❌ Error: route_name, date, and duration_hours are required for adding routes"
        
        return add_new_route(route_name, date, duration_hours, day_of_week)
    
    else:
        return f"""❌ Unknown action: {action}
        
Available actions:
• "status" - Check system health
• "reset" - Reset system to initial state
• "optimize" - Run weekly optimization  
• "update_availability" - Update driver availability
• "add_route" - Add new route

Example usage:
handle_scheduling_request("status")
handle_scheduling_request("update_availability", driver_name="Fröhlacher, Hubert", date="2025-07-07", available=False)
handle_scheduling_request("add_route", route_name="999TEST", date="2025-07-09", duration_hours=8.5)
"""


# Example usage for OpenAI Assistant
if __name__ == "__main__":
    # Test the functions
    print("=== Driver Scheduling System Test ===")
    
    # Check status
    print("\n1. Checking System Status:")
    print(handle_scheduling_request("status"))
    
    # Example: Make driver unavailable (creates F entry)
    print("\n2. Making Driver Unavailable:")
    print(handle_scheduling_request(
        "update_availability", 
        driver_name="Fröhlacher, Hubert", 
        date="2025-07-07", 
        available=False
    ))
    
    # Example: Add new route
    print("\n3. Adding New Route:")
    print(handle_scheduling_request(
        "add_route",
        route_name="TEST123",
        date="2025-07-09", 
        duration_hours=7.5,
        day_of_week="wednesday"
    ))
    
    # Reset system
    print("\n4. Resetting System:")
    print(handle_scheduling_request("reset"))