# Fixed Route Assignment API Endpoints

## Overview

Complete API endpoints for managing fixed driver-route assignments with automatic optimization and Google Sheets updates after each change.

## Base URL
```
http://localhost:5000/api/v1/assistant
```

## Endpoints

### 1. Create Fixed Route Assignment
**POST** `/create-fixed-route`

Creates a new fixed driver-route assignment and automatically reruns optimization with Google Sheets update.

#### Request Body
```json
{
  "driver_name": "Genäuß, Thomas",
  "route_pattern": "431oS",
  "priority": 1,
  "day_of_week": "monday",
  "notes": "Experienced driver for Monday routes"
}
```

#### Parameters
- `driver_name` (string, required): Exact driver name from database
- `route_pattern` (string, required): Route pattern like "452SA", "431oS"
- `priority` (integer, optional): Priority level (1 = highest priority, default: 1)
- `day_of_week` (string, optional): "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", or "any" (default: "any")
- `notes` (string, optional): Business reason for assignment

#### Response
```json
{
  "status": "success",
  "message": "Fixed route created and optimization completed: Genäuß, Thomas -> 431oS",
  "fixed_route_id": 2,
  "driver_name": "Genäuß, Thomas",
  "route_pattern": "431oS",
  "priority": 1,
  "day_of_week": "monday",
  "optimization_completed": true,
  "sheets_updated": true,
  "total_routes_assigned": 39
}
```

#### Example cURL
```bash
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Klagenfurt - Samstagsfahrer",
    "route_pattern": "452SA",
    "priority": 1,
    "day_of_week": "saturday",
    "notes": "Traditional Saturday route assignment"
  }'
```

---

### 2. Get All Fixed Route Assignments
**GET** `/fixed-routes`

Returns all active fixed driver-route assignments.

#### Response
```json
{
  "status": "success",
  "fixed_routes": [
    {
      "id": 1,
      "driver_id": 21,
      "route_pattern": "452SA",
      "priority": 1,
      "day_of_week": "saturday",
      "effective_start_date": null,
      "effective_end_date": null,
      "is_active": true,
      "notes": "Traditional Saturday route assignment",
      "created_at": "2025-08-19T06:11:06.389849",
      "updated_at": "2025-08-19T06:11:06.389849",
      "driver_name": "Klagenfurt - Samstagsfahrer"
    }
  ],
  "count": 1
}
```

#### Example cURL
```bash
curl -X GET "http://localhost:5000/api/v1/assistant/fixed-routes"
```

---

### 3. Update Fixed Route Assignment
**PUT** `/fixed-routes/{fixed_route_id}`

Updates an existing fixed driver-route assignment and automatically reruns optimization with Google Sheets update.

#### Request Body
```json
{
  "driver_name": "Bandzi, Attila",
  "route_pattern": "452SA",
  "priority": 2,
  "day_of_week": "saturday",
  "notes": "Updated assignment with backup driver"
}
```

#### Response
```json
{
  "status": "success",
  "message": "Fixed route updated and optimization completed: Bandzi, Attila -> 452SA",
  "fixed_route_id": 1,
  "driver_name": "Bandzi, Attila",
  "route_pattern": "452SA",
  "priority": 2,
  "day_of_week": "saturday",
  "optimization_completed": true,
  "sheets_updated": true,
  "total_routes_assigned": 39
}
```

#### Example cURL
```bash
curl -X PUT "http://localhost:5000/api/v1/assistant/fixed-routes/1" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Bandzi, Attila",
    "route_pattern": "452SA",
    "priority": 2,
    "day_of_week": "saturday",
    "notes": "Updated to backup driver"
  }'
```

---

### 4. Delete Fixed Route Assignment
**DELETE** `/fixed-routes/{fixed_route_id}`

Deletes a fixed driver-route assignment and automatically reruns optimization with Google Sheets update.

#### Response
```json
{
  "status": "success",
  "message": "Fixed route ID 1 deleted and optimization completed",
  "optimization_completed": true,
  "sheets_updated": true,
  "total_routes_assigned": 39
}
```

#### Example cURL
```bash
curl -X DELETE "http://localhost:5000/api/v1/assistant/fixed-routes/1"
```

---

### 5. Get System Status (includes Fixed Routes)
**GET** `/status`

Returns system status including fixed routes count.

#### Response
```json
{
  "status": "operational",
  "drivers_count": 21,
  "fixed_routes_count": 2,
  "or_tools_enabled": true,
  "google_sheets_integration": true,
  "fixed_routes_enabled": true
}
```

#### Example cURL
```bash
curl -X GET "http://localhost:5000/api/v1/assistant/status"
```

---

## Automatic Workflow

Each endpoint that modifies fixed routes triggers the following automatic workflow:

1. **Modify Fixed Route**: Create, update, or delete the fixed route assignment
2. **Fetch Current Data**: Get all drivers, routes, availability, and updated fixed routes
3. **Run Enhanced Optimization**: Execute two-phase optimization (fixed routes first, then OR-Tools)
4. **Save Results**: Store optimized assignments in database
5. **Update Google Sheets**: Send complete driver grid to external Google Sheets via Cloud Function
6. **Return Results**: Provide comprehensive response with optimization status

## Priority System

- **Priority 1**: Highest priority (assigned first)
- **Priority 2**: Second priority (assigned if Priority 1 driver unavailable)
- **Priority N**: Lower priorities as fallback options

## Day-of-Week Logic

- **"monday", "tuesday", etc.**: Fixed route only applies on that specific day
- **"any"**: Fixed route applies to any day the route appears

## Business Use Cases

### 1. Traditional Route Assignments
```bash
# Saturday specialist always gets Saturday routes
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Klagenfurt - Samstagsfahrer",
    "route_pattern": "452SA",
    "day_of_week": "saturday",
    "notes": "Traditional Saturday route assignment"
  }'
```

### 2. Experienced Driver Preferences
```bash
# Senior driver gets challenging Monday routes
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Genäuß, Thomas",
    "route_pattern": "431oS",
    "day_of_week": "monday",
    "notes": "Experienced driver for challenging routes"
  }'
```

### 3. Backup Driver System
```bash
# Create primary driver assignment
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Primary Driver",
    "route_pattern": "EXPRESS",
    "priority": 1,
    "notes": "Primary express route driver"
  }'

# Create backup driver assignment
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Backup Driver",
    "route_pattern": "EXPRESS", 
    "priority": 2,
    "notes": "Backup if primary unavailable"
  }'
```

## Error Handling

All endpoints include comprehensive error handling:

- **404**: Driver not found
- **500**: Database errors, optimization failures, Google Sheets update failures
- **422**: Invalid request data

## Logs and Monitoring

Each operation generates detailed logs showing:
- Fixed route modifications
- Optimization process (FIXED vs OPTIMIZED assignments)
- Google Sheets update status
- Performance metrics

## Integration Notes

- **Automatic Updates**: No manual intervention required after changing fixed routes
- **Real-time Sheets**: Google Sheets updated immediately after each change
- **Business Intelligence**: Clear logs distinguish between fixed and optimized assignments
- **Fallback Protection**: If fixed driver unavailable, route automatically optimized
- **Complete Workflow**: Database → Optimization → Google Sheets in single operation

This system provides complete control over driver-route assignments while maintaining the efficiency of mathematical optimization for all other routes.