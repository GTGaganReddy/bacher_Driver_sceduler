# Fixed Driver-Route Assignment Implementation

## Overview

The system now supports priority-based fixed driver-route assignments where specific drivers are assigned to specific routes first, with fallback to general optimization if the fixed driver is unavailable.

## Database Schema

### New Table: `fixed_driver_routes`
```sql
CREATE TABLE fixed_driver_routes (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER REFERENCES drivers(driver_id) ON DELETE CASCADE,
    route_pattern VARCHAR(50) NOT NULL,      -- Route pattern like '452SA', '431oS'
    priority INTEGER DEFAULT 1,              -- 1 = highest priority
    day_of_week VARCHAR(20),                 -- 'monday', 'tuesday', etc. or 'any'
    effective_start_date DATE,               -- When assignment becomes effective
    effective_end_date DATE,                 -- When assignment expires (NULL = permanent)
    is_active BOOLEAN DEFAULT TRUE,          -- Can be disabled without deletion
    notes TEXT,                             -- Business reason for assignment
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## How Fixed Routes Work

### 1. Priority Assignment Process
1. **Phase 1: Fixed Route Assignment**
   - Check if route has fixed assignments in `fixed_driver_routes` table
   - Sort candidates by priority (1 = highest priority)
   - For each candidate:
     - Check day of week compatibility
     - Check driver availability for the specific date
     - Check remaining driver hours capacity
     - If all checks pass: assign route to fixed driver
     - If not: try next priority candidate

2. **Phase 2: OR-Tools Optimization**
   - Remaining unassigned routes go to general optimization
   - OR-Tools assigns these routes optimally among available drivers
   - Considers reduced capacity from fixed route assignments

### 2. Fallback Behavior
- **Fixed driver available**: Route assigned via fixed rule
- **Fixed driver unavailable**: Route automatically goes to optimization pool
- **Fixed driver insufficient hours**: Route goes to optimization pool
- **No fixed assignment**: Route handled by normal optimization

## API Endpoints

### Create Fixed Route Assignment
```
POST /api/v1/assistant/create-fixed-route
Content-Type: application/json

{
  "driver_name": "Genäuß, Thomas",
  "route_pattern": "431oS",
  "priority": 1,
  "day_of_week": "monday",
  "notes": "Experienced driver for Monday routes"
}
```

### Get Fixed Routes
```
GET /api/v1/assistant/fixed-routes

Response:
{
  "status": "success",
  "fixed_routes": [
    {
      "id": 1,
      "driver_id": 5,
      "driver_name": "Genäuß, Thomas",
      "route_pattern": "431oS",
      "priority": 1,
      "day_of_week": "monday",
      "notes": "Experienced driver for Monday routes",
      "is_active": true
    }
  ],
  "count": 1
}
```

### Delete Fixed Route
```
DELETE /api/v1/assistant/fixed-routes/{id}

Response:
{
  "status": "success",
  "message": "Fixed route ID 1 deleted successfully"
}
```

## Enhanced Optimization Algorithm

### New Function: `run_ortools_optimization_with_fixed_routes()`
```python
def run_ortools_optimization_with_fixed_routes(drivers, routes, availability, fixed_routes=None):
    """
    Enhanced OR-Tools optimization with priority fixed assignments
    
    Process:
    1. Parse fixed route rules and create lookup table
    2. For each date sequentially:
       - Apply fixed route assignments first
       - Run OR-Tools optimization for remaining routes
       - Update driver capacity tracking
    3. Combine fixed and optimized assignments
    """
```

### Assignment Types
- **Fixed Assignment**: Route assigned via fixed rule (`assignment_type: 'fixed'`)
- **Optimized Assignment**: Route assigned via OR-Tools (`assignment_type: 'optimized'`)

## Example Usage

### 1. Setting Up Fixed Routes
```bash
# Make Saturday route 452SA always go to Klagenfurt - Samstagsfahrer
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Klagenfurt - Samstagsfahrer",
    "route_pattern": "452SA",
    "priority": 1,
    "day_of_week": "saturday",
    "notes": "Traditional Saturday route assignment"
  }'

# Make Monday route 431oS prefer Genäuß, Thomas
curl -X POST "http://localhost:5000/api/v1/assistant/create-fixed-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_name": "Genäuß, Thomas",
    "route_pattern": "431oS",
    "priority": 1,
    "day_of_week": "monday",
    "notes": "Experienced driver for Monday routes"
  }'
```

### 2. Running Optimization with Fixed Routes
```bash
# This will now apply fixed routes first, then optimize remaining
curl -X POST "http://localhost:5000/api/v1/assistant/optimize-week" \
  -H "Content-Type: application/json" \
  -d '{"week_start": "2025-07-07"}'
```

### 3. Logs Show Fixed vs Optimized Assignments
```
2025-08-19 05:53:26,896 - services.optimizer - INFO - FIXED: Assigned 452SA to Klagenfurt - Samstagsfahrer (10.0h). Remaining: 150.0h
2025-08-19 05:53:26,898 - services.optimizer - INFO - OPTIMIZED: Assigned 431oS to Blaskovic, Nenad (11.0h)
```

## Benefits

### 1. Business Rule Flexibility
- **Preserve Traditional Assignments**: Keep experienced drivers on familiar routes
- **Seasonal Adjustments**: Different fixed routes for peak/low seasons
- **Regulatory Compliance**: Ensure specific qualifications for certain routes
- **Customer Preferences**: Maintain consistent driver-customer relationships

### 2. Operational Reliability
- **Fallback Protection**: If fixed driver unavailable, optimization handles assignment
- **Capacity Aware**: Fixed assignments reduce available hours for optimization
- **Priority Handling**: Multiple drivers can be configured for same route with priority order

### 3. System Intelligence
- **Hybrid Approach**: Combines business rules with mathematical optimization
- **Transparent Assignment**: Logs show whether assignment was fixed or optimized
- **Performance Tracking**: Can measure effectiveness of fixed vs optimized assignments

## Integration with Existing System

### 1. Database Service Extensions
- Added `get_fixed_driver_routes()`, `create_fixed_driver_route()`, `delete_fixed_driver_route()` methods
- Automatic table creation in database initialization
- Indexed for performance on route patterns and active status

### 2. Assistant API Integration
- All existing endpoints now use enhanced optimizer automatically
- Weekly optimization includes fixed route processing
- Status endpoint shows fixed routes count

### 3. Backward Compatibility
- Original `run_ortools_optimization()` function still available
- If no fixed routes provided, system behaves exactly as before
- Existing API endpoints continue to work unchanged

## Future Enhancements

### 1. Advanced Fixed Route Features
- **Time-based Rules**: Different fixed assignments for different time periods
- **Route Groups**: Assign driver to multiple related routes as a group
- **Conditional Logic**: "If driver A unavailable, try driver B, else optimize"

### 2. BubbleGPT Integration
- **Natural Language**: "Make Genäuß, Thomas always handle Monday routes"
- **Temporary Rules**: "For this week only, assign route 431oS to Bandzi, Attila"
- **Rule Management**: "Show me all fixed routes" via conversational interface

### 3. Analytics Integration
- **Performance Metrics**: Compare fixed vs optimized assignment efficiency
- **Utilization Analysis**: Track how often fixed rules are applied vs fallback
- **Business Intelligence**: Optimize fixed rules based on historical performance

This implementation provides the foundation for intelligent, business-rule-aware optimization while maintaining the flexibility and mathematical rigor of OR-Tools optimization.