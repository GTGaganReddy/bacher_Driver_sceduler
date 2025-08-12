# Delete/Remove Route Endpoint

## Endpoint Details
**URL:** `POST /api/v1/assistant/remove-route`  
**Content-Type:** `application/json`

## Request Format
```json
{
  "route_name": "ROUTE_NAME",
  "date": "YYYY-MM-DD"
}
```

## Examples

### Remove a specific route:
```json
{
  "route_name": "500",
  "date": "2025-07-09"
}
```

### Remove a test route:
```json
{
  "route_name": "TEST_ROUTE",
  "date": "2025-07-08"
}
```

## Response Format

### Success Response:
```json
{
  "status": "success",
  "route_removed": {
    "name": "500",
    "date": "2025-07-09",
    "id": 48
  },
  "total_assignments": 45,
  "total_routes": 45,
  "google_sheets_updated": true
}
```

### Error Response (Route Not Found):
```json
{
  "detail": "404: Route '500' on 2025-07-09 not found"
}
```

## What Happens When You Delete a Route:

1. **Database Deletion:** Route is permanently removed from the routes table
2. **Reoptimization:** OR-Tools runs complete weekly optimization with remaining routes
3. **Assignment Updates:** Driver assignments are recalculated optimally
4. **Google Sheets Update:** Updated schedule exported to your Google Sheets
5. **Response:** Returns confirmation with new totals

## Complete Working Example:

```bash
curl -X POST "http://your-repl-url/api/v1/assistant/remove-route" \
-H "Content-Type: application/json" \
-d '{
  "route_name": "500",
  "date": "2025-07-09"
}'
```