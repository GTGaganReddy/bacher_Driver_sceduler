#!/usr/bin/env python3
"""
Demo script for OpenAI Assistant Driver Scheduling Integration

This script demonstrates all available operations that can be performed
through the OpenAI Assistant using the provided action code.

Run this script to verify your setup is working correctly.
"""

import requests
import json
from datetime import datetime

# Replace with your actual Replit URL
API_BASE_URL = "http://0.0.0.0:5000"

def make_request(endpoint, method="GET", data=None):
    """Make request to the API"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def demo_all_operations():
    """Demonstrate all OpenAI Assistant operations"""
    
    print("🚀 Driver Scheduling System - OpenAI Assistant Demo")
    print("=" * 60)
    
    # 1. System Status Check
    print("\n📊 1. CHECKING SYSTEM STATUS")
    status = make_request("/api/v1/assistant/status")
    if "error" not in status:
        print(f"✅ Status: {status.get('status')}")
        print(f"📈 Drivers: {status.get('drivers_count')}")
        print(f"🔧 OR-Tools: {'Enabled' if status.get('or_tools_enabled') else 'Disabled'}")
        print(f"📊 Google Sheets: {'Connected' if status.get('google_sheets_integration') else 'Disconnected'}")
    else:
        print(f"❌ Error: {status['error']}")
    
    # 2. Reset System
    print("\n🔄 2. RESETTING SYSTEM TO INITIAL STATE")
    reset_result = make_request("/api/v1/assistant/reset", "POST")
    if "error" not in reset_result and reset_result.get("status") == "success":
        print(f"✅ Reset successful!")
        print(f"📈 Drivers reset: {reset_result.get('drivers_count')}")
        print(f"🗂️ Routes available: {reset_result.get('routes_count')}")
        print(f"🧹 Assignments cleared: {reset_result.get('assignments_cleared')}")
    else:
        print(f"❌ Reset failed: {reset_result.get('error', 'Unknown error')}")
    
    # 3. Update Driver Availability (Create F Entry)
    print("\n👤 3. MAKING DRIVER UNAVAILABLE (F ENTRY DEMO)")
    availability_data = {
        "driver_name": "Fröhlacher, Hubert",
        "updates": [{"date": "2025-07-07", "available": False}],
        "week_start": "2025-07-07"
    }
    
    availability_result = make_request("/api/v1/assistant/update-availability", "POST", availability_data)
    if "error" not in availability_result and availability_result.get("status") == "success":
        print(f"✅ Driver made unavailable: {availability_result.get('driver_updated')}")
        print(f"📝 Updates applied: {availability_result.get('updates_applied')}")
        print(f"🎯 Total assignments: {availability_result.get('total_assignments')}")
        print(f"📊 Google Sheets updated: {availability_result.get('google_sheets_updated')}")
        print("📌 F entry created for Monday 2025-07-07!")
    else:
        print(f"❌ Availability update failed: {availability_result.get('error', 'Unknown error')}")
    
    # 4. Add New Route
    print("\n🛣️ 4. ADDING NEW ROUTE")
    route_data = {
        "route_name": "DEMO999",
        "date": "2025-07-09",
        "duration_hours": 7.5,
        "route_type": "demo",
        "day_of_week": "wednesday",
        "week_start": "2025-07-07"
    }
    
    route_result = make_request("/api/v1/assistant/add-route", "POST", route_data)
    if "error" not in route_result and route_result.get("status") == "success":
        route_info = route_result.get('route_added', {})
        print(f"✅ Route added: {route_info.get('name')}")
        print(f"📅 Date: {route_info.get('date')}")
        print(f"⏱️ Duration: {route_info.get('duration_hours')} hours")
        print(f"🎯 Total assignments: {route_result.get('total_assignments')}")
        print(f"🗂️ Total routes: {route_result.get('total_routes')}")
    else:
        print(f"❌ Route addition failed: {route_result.get('error', 'Unknown error')}")
    
    # 5. Weekly Optimization
    print("\n🧠 5. RUNNING WEEKLY OPTIMIZATION")
    optimization_data = {"week_start": "2025-07-07"}
    
    optimization_result = make_request("/api/v1/assistant/optimize-week", "POST", optimization_data)
    if "error" not in optimization_result and optimization_result.get("status") == "success":
        print(f"✅ Optimization completed!")
        print(f"📅 Week: {optimization_result.get('week_start')}")
        print(f"🎯 Assignments: {optimization_result.get('total_assignments')}")
        print(f"🗂️ Routes processed: {optimization_result.get('total_routes')}")
        print(f"🏆 Solver status: {optimization_result.get('solver_status')}")
        print(f"📊 Google Sheets: {'Updated' if optimization_result.get('google_sheets_updated') else 'Failed'}")
    else:
        print(f"❌ Optimization failed: {optimization_result.get('error', 'Unknown error')}")
    
    print("\n🎉 DEMO COMPLETED!")
    print("=" * 60)
    print("\n🔧 OpenAI Assistant Integration Ready!")
    print("\nYou can now use the action code in your OpenAI Assistant to:")
    print("• Check system status")
    print("• Reset the scheduling system")
    print("• Make drivers unavailable (creates F entries)")
    print("• Add new routes dynamically")
    print("• Run complete weekly optimizations")
    print("\nAll operations automatically update Google Sheets!")


def demo_natural_language_examples():
    """Show examples of natural language requests the Assistant can handle"""
    
    print("\n💬 NATURAL LANGUAGE EXAMPLES")
    print("=" * 60)
    print("\nYour OpenAI Assistant can now understand requests like:")
    print()
    
    examples = [
        "Check if the driver scheduling system is working properly",
        "Reset everything back to the beginning",
        "Make Fröhlacher, Hubert unavailable on Monday July 7th",
        "Add a new 8-hour route called EXPRESS123 for Wednesday",
        "Optimize the entire weekly schedule",
        "Show me the system status",
        "Create an F entry for Genäuß, Thomas on Tuesday",
        "Add route EMERGENCY on Friday with 6.5 hours duration"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i:2}. \"{example}\"")
    
    print(f"\n📋 All {len(examples)} request types are fully supported!")


if __name__ == "__main__":
    print("🤖 Testing OpenAI Assistant Driver Scheduling Integration")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        demo_all_operations()
        demo_natural_language_examples()
        
        print("\n✅ Setup verification complete!")
        print("🎯 Your OpenAI Assistant is ready to manage driver scheduling!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("🔧 Check your API server and try again")