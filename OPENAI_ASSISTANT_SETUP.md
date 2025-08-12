# OpenAI Assistant Setup Guide for Driver Scheduling System

This guide explains how to integrate the Driver Scheduling Backend with OpenAI Assistant using the provided action code.

## 🚀 Quick Setup

### 1. **Get Your API URL**
Your FastAPI server is running at: `http://0.0.0.0:5000`

For external access, use your Replit project URL:
```
https://YOUR-REPL-NAME.YOUR-USERNAME.repl.co
```

### 2. **Update the Action Code**
In `openai_assistant_action.py`, replace:
```python
def __init__(self, base_url: str = "YOUR_API_BASE_URL"):
```

With your actual URL:
```python
def __init__(self, base_url: str = "https://YOUR-REPL-NAME.YOUR-USERNAME.repl.co"):
```

### 3. **Create OpenAI Assistant Action**
Copy the entire `openai_assistant_action.py` content into your OpenAI Assistant action configuration.

## 📋 Available Endpoints

Your system now supports **5 main operations**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/assistant/status` | GET | Check system health |
| `/api/v1/assistant/reset` | POST | Reset system to initial state |
| `/api/v1/assistant/optimize-week` | POST | Run weekly optimization |
| `/api/v1/assistant/update-availability` | POST | Update driver availability (advanced) |
| `/api/v1/assistant/update-driver-availability` | POST | **NEW!** Simple single driver update |
| `/api/v1/assistant/add-route` | POST | Add new route and reoptimize |

## 🎯 Usage Examples

### **System Status Check**
```python
handle_scheduling_request("status")
```
Returns system health, driver count, and integration status.

### **Reset System** ⚡ **NEW FEATURE**
```python
handle_scheduling_request("reset")
```
- Clears all previous assignments
- Resets all drivers to available (except Sunday)
- Returns system to clean initial state

### **Update Driver Availability (F Entries)** ⚡ **FIXED REQUEST FORMAT**
```python
# Direct API call format (what you should use):
{
  "driver_name": "Genäuß, Thomas",
  "date": "2025-07-07",
  "available": false
}

# Or using the action function:
handle_scheduling_request(
    "update_availability", 
    driver_name="Fröhlacher, Hubert", 
    date="2025-07-07", 
    available=False
)
```
- Makes driver unavailable on specified date
- Creates F entry in Google Sheets (route="F", hour="0:00")
- Reoptimizes entire week automatically
- **Now supports both simple and advanced request formats**

### **Add New Route**
```python
handle_scheduling_request(
    "add_route",
    route_name="TEST99",
    date="2025-07-09", 
    duration_hours=8.5
)
```
- Adds route to database
- Automatically assigns to optimal driver
- Updates Google Sheets with new assignments

### **Weekly Optimization**
```python
handle_scheduling_request("optimize", week_start="2025-07-07")
```
- Runs complete OR-Tools optimization
- Processes all 21 drivers and routes
- Exports results to Google Sheets

## 🔧 Driver Names Reference

Use these exact names for driver operations:

- `"Bandzi, Attila"`
- `"Blaskovic, Nenad"`
- `"Fröhlacher, Hubert"`
- `"Genäuß, Thomas"`
- `"Granitzer, Hermann"`
- `"Hinteregger, Manfred"`
- `"Kandolf, Alfred"`
- `"Klagenfurt - Fahrer"`
- `"Klagenfurt - Samstagsfahrer"`
- `"Konheiser, Elisabeth"`
- `"Lauhart, Egon"`
- `"Madrutter, Anton"`
- `"Merz, Matthias"`
- `"Niederbichler, Daniel"`
- `"Nurikic, Ervin"`
- `"Obersteiner, Roland"`
- `"Rauter, Agnes Zita"`
- `"Simon, Otto"`
- `"Struckl, Stefan"`
- `"Sulics, Egon"`
- `"Thamer, Karl"`

## 🎨 Natural Language Integration

The Assistant can now understand natural language requests like:

- **"Check if the scheduling system is working"** → `status`
- **"Reset everything back to the beginning"** → `reset`
- **"Make Fröhlacher, Hubert unavailable on Monday"** → `update_availability`
- **"Add a new 6-hour route called EXPRESS on Wednesday"** → `add_route`
- **"Optimize the entire week schedule"** → `optimize`

## 📊 Response Format

All operations return structured responses:

### ✅ Success Response Example
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "drivers_count": 21,
  "total_assignments": 43,
  "google_sheets_updated": true
}
```

### ❌ Error Response Example
```json
{
  "error": "Driver 'Invalid Name' not found"
}
```

## 🔄 Complete Workflow Example

```python
# 1. Check system health
status = handle_scheduling_request("status")

# 2. Reset to clean state
reset_result = handle_scheduling_request("reset")

# 3. Make a driver unavailable (creates F entry)
availability = handle_scheduling_request(
    "update_availability", 
    driver_name="Genäuß, Thomas", 
    date="2025-07-08", 
    available=False
)

# 4. Add emergency route
new_route = handle_scheduling_request(
    "add_route",
    route_name="EMERGENCY",
    date="2025-07-10", 
    duration_hours=4.0
)

# 5. Run final optimization
optimization = handle_scheduling_request("optimize")
```

## 🎯 Key Features

### **F Entry Support** ✅
- Unavailable drivers automatically get `route="F"` and `hour="0:00"`
- Exported directly to Google Sheets
- No manual intervention required

### **Automatic Reoptimization** ✅
- Every change triggers complete system reoptimization
- All 21 drivers and routes recalculated
- Results immediately sent to Google Sheets

### **Error Handling** ✅
- Clear error messages for invalid operations
- Automatic validation of driver names and dates
- Fallback responses for system issues

### **Real-time Integration** ✅
- Changes reflect immediately in Google Sheets
- No caching delays or batch processing
- Live system updates

## 🚨 Important Notes

1. **Exact Driver Names**: Use the exact names from the reference list above
2. **Date Format**: Always use `YYYY-MM-DD` format (e.g., `2025-07-07`)
3. **Reset Functionality**: The reset endpoint clears ALL data - use carefully
4. **Duration Hours**: Use decimal format (e.g., `6.5` for 6 hours 30 minutes)
5. **System Scope**: All operations work within July 7-13, 2025 timeframe

## 📞 Testing Your Setup

Run this test in your OpenAI Assistant:

```python
# Test connection
print(handle_scheduling_request("status"))

# If successful, you should see:
# "✅ Driver Scheduling System Status: OPERATIONAL"
```

Your Driver Scheduling System is now fully integrated with OpenAI Assistant! 🎉