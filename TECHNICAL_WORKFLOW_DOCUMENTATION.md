# Technical Workflow Documentation: BubbleGPT Assistant → Backend → Google Cloud Function → Google Sheets

## System Architecture Overview

```
BubbleGPT Assistant → FastAPI Backend → PostgreSQL → OR-Tools → Google Cloud Function → Google Sheets
                      (Replit)         (Supabase)   (Optimization)  (Sheet Update)    (Final Output)
```

## 1. Component Architecture

### 1.1 BubbleGPT Assistant (External Client)
- **Role**: External AI Assistant that sends HTTP requests to the backend
- **Technology**: OpenAI GPT-based assistant with function calling capabilities
- **Communication**: JSON over HTTP/HTTPS
- **Base URL**: `https://YOUR_REPLIT_APP.repl.co/api/v1/assistant`

### 1.2 FastAPI Backend (Replit)
- **Framework**: FastAPI with AsyncIO architecture
- **Host**: `0.0.0.0:5000` (production deployment on Cloud Run)
- **Database**: AsyncPG connection pool to Supabase PostgreSQL
- **Optimization Engine**: Google OR-Tools CP-SAT solver
- **External Integration**: HTTPX client for Google Cloud Function calls

### 1.3 PostgreSQL Database (Supabase)
- **Host**: `db.nqwyglxhvhlrviknykmt.supabase.co:5432`
- **Connection**: Session pooler for production stability
- **Tables**: `drivers`, `driver_availability`, `routes`, `assignments`
- **Data**: Authentic logistics data for July 7-13, 2025 period

### 1.4 Google Cloud Function (GCF)
- **URL**: `https://us-central1-driver-schedule-updater.cloudfunctions.net/update_sheet`
- **Method**: POST with JSON payload
- **Role**: Bridge between FastAPI backend and Google Sheets API
- **Authentication**: Service account credentials for Sheets access

### 1.5 Google Sheets (Final Output)
- **Format**: Driver grid with 21 drivers × 7 days matrix
- **Updates**: Complete overwrite with optimized assignments
- **Data Types**: Route assignments, "F" entries for unavailable drivers, blank entries

## 2. API Endpoints and Data Flow

### 2.1 System Status Check
```
GET /api/v1/assistant/status
```
**Request**: None (GET request)
**Response**:
```json
{
  "status": "operational",
  "drivers_count": 21,
  "or_tools_enabled": true,
  "google_sheets_integration": true
}
```
**Processing**: Direct database query for driver count, no optimization or sheet update.

### 2.2 System Reset with Auto-Optimization
```
POST /api/v1/assistant/reset
```
**Request**: None (empty JSON body)
**Internal Workflow**:
1. Clear assignments table: `DELETE FROM assignments`
2. Clear manually added routes: `DELETE FROM routes WHERE date BETWEEN '2025-07-07' AND '2025-07-13' AND created_at > '2025-08-11 21:10:00'`
3. Reset driver availability: `UPDATE driver_availability SET available = true WHERE date BETWEEN '2025-07-07' AND '2025-07-12'`
4. Keep Sunday unavailable: `UPDATE driver_availability SET available = false WHERE date = '2025-07-13'`
5. Run OR-Tools optimization with reset data
6. Update Google Sheets via GCF
7. Save new assignments to database

**Response**:
```json
{
  "status": "success",
  "message": "System reset to initial state and optimization completed",
  "drivers_count": 21,
  "routes_count": 42,
  "assignments_cleared": true,
  "availability_reset": true,
  "routes_reset": true,
  "optimization_run": true,
  "sheets_updated": true
}
```

### 2.3 Weekly Optimization
```
POST /api/v1/assistant/optimize-week
```
**Request**:
```json
{
  "week_start": "2025-07-07"
}
```
**Internal Workflow**:
1. Fetch all drivers: `SELECT * FROM drivers`
2. Fetch routes in date range: `SELECT * FROM routes WHERE date BETWEEN week_start AND week_end`
3. Fetch availability: `SELECT * FROM driver_availability WHERE date BETWEEN week_start AND week_end`
4. Run sequential OR-Tools optimization (day-by-day)
5. Generate driver-route assignments with capacity tracking
6. Send complete driver grid to Google Cloud Function
7. Save assignments: `INSERT INTO assignments (week_start, driver_id, route_id, ...)`

**Response**:
```json
{
  "status": "success",
  "week": "2025-07-07 to 2025-07-13",
  "total_assignments": 42,
  "total_routes": 42,
  "google_sheets_updated": true,
  "solver_status": "OPTIMAL"
}
```

### 2.4 Update Driver Availability (Simplified)
```
POST /api/v1/assistant/update-driver-availability
```
**Request**:
```json
{
  "driver_name": "Genäuß, Thomas",
  "date": "2025-07-07",
  "available": false
}
```
**Internal Workflow**:
1. Find driver: `SELECT driver_id FROM drivers WHERE name = 'Genäuß, Thomas'`
2. Update availability: `INSERT INTO driver_availability (driver_id, date, available) VALUES (...) ON CONFLICT UPDATE`
3. Re-run complete weekly optimization for July 7-13, 2025
4. Generate "F" entries for unavailable drivers in optimization result
5. Send updated driver grid to Google Cloud Function
6. Save new assignments

**Response**:
```json
{
  "status": "success",
  "driver_updated": "Genäuß, Thomas",
  "updates_applied": [{"date": "2025-07-07", "available": false}],
  "total_assignments": 43,
  "total_routes": 42,
  "google_sheets_updated": true
}
```

### 2.5 Add Single Route (Simplified)
```
POST /api/v1/assistant/add-single-route
```
**Request**:
```json
{
  "route_name": "500",
  "date": "2025-07-09",
  "duration_hours": 6.5
}
```
**Internal Workflow**:
1. Determine day of week from date
2. Create route details JSON: `{"duration": "6:30", "route_code": "500", "type": "regular"}`
3. Insert route: `INSERT INTO routes (date, route_name, details) VALUES (...)`
4. Re-run complete weekly optimization
5. Assign new route to optimal driver based on capacity and availability
6. Send updated assignments to Google Cloud Function
7. Save new assignments

**Response**:
```json
{
  "status": "success",
  "route_added": {
    "name": "500",
    "date": "2025-07-09",
    "duration_hours": 6.5,
    "id": 53
  },
  "total_assignments": 43,
  "total_routes": 43,
  "google_sheets_updated": true
}
```

### 2.6 Remove Route
```
POST /api/v1/assistant/remove-route
```
**Request**:
```json
{
  "route_name": "500",
  "date": "2025-07-09"
}
```
**Internal Workflow**:
1. Find and delete route: `DELETE FROM routes WHERE route_name = '500' AND date = '2025-07-09' RETURNING *`
2. Re-run optimization with remaining routes
3. Redistribute driver assignments optimally
4. Send updated assignments to Google Cloud Function
5. Save new assignments

**Response**:
```json
{
  "status": "success",
  "route_removed": {
    "name": "500",
    "date": "2025-07-09",
    "id": 53
  },
  "total_assignments": 42,
  "total_routes": 42,
  "google_sheets_updated": true
}
```

## 3. OR-Tools Optimization Engine

### 3.1 Sequential Day-by-Day Algorithm
- **Solver**: Google OR-Tools CP-SAT with SCIP backend
- **Approach**: Chronological processing (July 7 → July 8 → ... → July 12)
- **Capacity Tracking**: Dynamic hour reduction after each day's assignments
- **Constraints**: Driver availability, monthly hour limits, route requirements

### 3.2 Optimization Process
1. **Data Parsing**: Convert database format to OR-Tools variables
2. **Driver Capacity**: Initialize remaining hours (default 160h/month per driver)
3. **Day-by-Day Solving**: 
   - Create fresh solver instance for each date
   - Apply availability constraints for that specific date
   - Assign routes to minimize cost (maximize efficiency)
   - Reduce driver remaining hours for subsequent days
4. **Saturday Constraint**: Force route 452SA to "Klagenfurt - Samstagsfahrer"
5. **Result Generation**: Convert solver output back to assignment format

### 3.3 Assignment Types
- **Regular Assignment**: Route assigned to available driver
- **F Entry**: Unavailable driver gets route="F", hour="0:00"
- **Blank Entry**: Available driver with no route assignment

## 4. Google Cloud Function Integration

### 4.1 Request Payload to GCF
```json
{
  "drivers_data": [
    {
      "driver": "Genäuß, Thomas",
      "route": "433oS",
      "hour": "11:00",
      "remaining_hour": "0:00",
      "date": "2025-07-07",
      "status": "update"
    },
    {
      "driver": "Fröhlacher, Hubert",
      "route": "F",
      "hour": "0:00",
      "remaining_hour": "0:00",
      "date": "2025-07-07",
      "status": "update"
    },
    {
      "driver": "Bandzi, Attila",
      "route": "",
      "hour": "",
      "remaining_hour": "0:00",
      "date": "2025-07-07",
      "status": "update"
    }
  ]
}
```

### 4.2 Complete Driver Grid Generation
- **Total Entries**: 147 (21 drivers × 7 days)
- **Assignment Types**: Assigned routes, "F" entries for unavailable drivers, blank entries for unassigned
- **Complete Overwrite**: Sends all 147 entries to ensure sheet consistency
- **Date Format**: YYYY-MM-DD for precise matching

### 4.3 GCF Response Handling
```json
{
  "status": "success",
  "message": "Sheet updated successfully",
  "entries_processed": 147
}
```
Backend interprets any successful HTTP 200 response as confirmation of sheet update.

## 5. Database Schema and Operations

### 5.1 Table Structure
```sql
-- Core driver information
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    monthly_hours_limit INTEGER DEFAULT 174,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Driver availability by date
CREATE TABLE driver_availability (
    id SERIAL PRIMARY KEY,
    driver_id INT REFERENCES drivers(driver_id),
    date DATE NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(driver_id, date)
);

-- Route definitions
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    route_name TEXT NOT NULL,
    details JSONB,  -- {"duration": "8:00", "route_code": "431oS", "type": "regular"}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Optimization results
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    driver_id INT REFERENCES drivers(driver_id),
    route_id INT REFERENCES routes(route_id),
    assignment_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 Data Operations
- **Insert Operations**: Route additions via API
- **Update Operations**: Driver availability changes
- **Delete Operations**: Route removals, system resets
- **Query Operations**: Fetching data for optimization

## 6. Error Handling and Resilience

### 6.1 Database Connection
- **Connection Pooling**: AsyncPG pool with 2-10 connections
- **Retry Logic**: Automatic reconnection on connection loss
- **Timeout Handling**: 60-second command timeout

### 6.2 OR-Tools Optimization
- **Solver Failure**: Returns error response if no feasible solution
- **Data Validation**: Checks for missing drivers or routes before optimization
- **Capacity Overflow**: Handles cases where driver hours exceed limits

### 6.3 Google Cloud Function
- **HTTP Timeout**: 30-second timeout for GCF requests
- **Retry Strategy**: Single attempt with error logging
- **Fallback**: Optimization proceeds even if sheet update fails

### 6.4 API Error Responses
```json
{
  "detail": "404: Route 'nonexistent' on 2025-07-09 not found"
}
```
Standard HTTP status codes with descriptive error messages.

## 7. Performance Characteristics

### 7.1 Optimization Speed
- **Typical Runtime**: 2-4 seconds for 42 routes, 21 drivers
- **Sequential Processing**: 5 separate solver instances (one per day)
- **Bottleneck**: OR-Tools constraint solving, not database operations

### 7.2 Database Performance
- **Query Speed**: Sub-100ms for typical data fetches
- **Connection Management**: Pool reuse for optimal performance
- **Indexing**: Primary keys and foreign keys for join optimization

### 7.3 Google Sheets Update
- **Payload Size**: ~147 entries per request
- **Update Time**: 2-3 seconds for complete sheet overwrite
- **Rate Limits**: Handled by Google Cloud Function service account

## 8. Security and Authentication

### 8.1 Database Security
- **Connection**: TLS-encrypted connection to Supabase
- **Authentication**: Password-based authentication with environment variables
- **Access Control**: Read/write access limited to application service account

### 8.2 Google Cloud Function Security
- **Authentication**: Service account with Google Sheets API access
- **Authorization**: Function-level permissions for sheet modification
- **Network**: HTTPS-only communication

### 8.3 API Security
- **Input Validation**: Pydantic models for request validation
- **SQL Injection**: Parameterized queries with AsyncPG
- **CORS**: Configured for cross-origin requests if needed

## 9. Monitoring and Logging

### 9.1 Application Logging
```python
# Structured logging with timestamps
2025-08-12 14:00:37,214 - services.optimizer - INFO - Assigned 431oS to Madrutter, Anton (11.0h). Remaining: 146.0h
2025-08-12 14:00:40,390 - services.google_sheets - INFO - Successfully updated Google Sheets with complete driver grid
```

### 9.2 Health Check Endpoints
- **Root Endpoint**: `GET /` - Basic health with database status
- **Rapid Health**: `GET /healthz` - Always-available deployment health check
- **Readiness**: `GET /ready` - Kubernetes/Cloud Run readiness probe
- **Liveness**: `GET /live` - Kubernetes/Cloud Run liveness probe

### 9.3 Operational Metrics
- **Response Times**: Tracked via FastAPI middleware
- **Database Connections**: Pool status monitoring
- **Optimization Success Rate**: Solver status tracking
- **Google Sheets Success Rate**: HTTP response code tracking

## 10. Deployment and Infrastructure

### 10.1 Production Deployment
- **Platform**: Google Cloud Run
- **Container**: FastAPI application with Python 3.11
- **Scaling**: Automatic scaling based on HTTP requests
- **Port Configuration**: PORT environment variable (set by Cloud Run)

### 10.2 Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:PASSWORD@db.nqwyglxhvhlrviknykmt.supabase.co:5432/postgres
SUPABASE_PASSWORD=your_supabase_password

# External Service
GCF_URL=https://us-central1-driver-schedule-updater.cloudfunctions.net/update_sheet

# Application Settings
DEBUG=false
PORT=5000
LOG_LEVEL=INFO
```

### 10.3 Dependencies
- **Core**: FastAPI, AsyncPG, OR-Tools, HTTPX, Pydantic
- **Database**: Supabase PostgreSQL client libraries
- **Optimization**: Google OR-Tools CP-SAT solver
- **HTTP Client**: HTTPX for async Google Cloud Function calls

## 11. Future Enhancements: Dynamic Constraint Management

### 11.1 Conversational Constraint Control via BubbleGPT Assistant
The next evolution of the system will enable dynamic constraint modification through natural language conversations with the BubbleGPT Assistant, moving beyond fixed OR-Tools constraints to a flexible, user-controlled optimization framework.

### 11.2 Current Constraint Limitations
**Fixed Constraints (Current System)**:
- Monthly hour limits: 174 hours per driver (hardcoded)
- Saturday route assignment: 452SA always assigned to "Klagenfurt - Samstagsfahrer" (hardcoded)
- Sequential optimization: Day-by-day processing (fixed algorithm)
- Availability constraints: Binary available/unavailable (simple boolean)

**Limitation**: Traditional OR-Tools implementations require constraint definitions at code level, making runtime modifications impossible without code changes.

### 11.3 Proposed Dynamic Constraint Architecture

#### 11.3.1 Constraint Configuration API
```json
POST /api/v1/assistant/configure-constraints
{
  "constraint_type": "driver_weekly_hours",
  "parameters": {
    "max_hours_per_week": 45,
    "apply_to_drivers": ["all", "specific_list"],
    "exceptions": [
      {"driver_name": "Klagenfurt - Samstagsfahrer", "max_hours": 20}
    ]
  },
  "effective_date": "2025-07-07",
  "description": "Reduce weekly hours to 45h per driver for better work-life balance"
}
```

#### 11.3.2 Conversational Constraint Management
**Natural Language Examples**:
- "Set maximum working hours per driver to 40 hours per week"
- "Allow driver Genäuß, Thomas to work maximum 35 hours this week only"
- "Remove the Saturday constraint for route 452SA - let any driver take it"
- "Add a new constraint: no driver can work more than 3 consecutive days"
- "Prioritize shorter routes for drivers over 50 years old"

#### 11.3.3 Constraint Types and Parameters

**1. Time-Based Constraints**:
```json
{
  "type": "time_constraint",
  "parameters": {
    "max_daily_hours": 12,
    "max_weekly_hours": 45,
    "min_rest_between_shifts": 8,
    "max_consecutive_days": 5
  }
}
```

**2. Route Assignment Rules**:
```json
{
  "type": "assignment_rule",
  "parameters": {
    "route_preferences": {
      "431oS": ["preferred_drivers": ["Driver A", "Driver B"]],
      "Saturday_routes": ["any_driver": true]
    },
    "driver_specializations": {
      "long_distance": ["Driver C", "Driver D"],
      "city_routes": ["Driver E", "Driver F"]
    }
  }
}
```

**3. Workload Distribution**:
```json
{
  "type": "workload_distribution",
  "parameters": {
    "balance_strategy": "equal_hours",
    "allow_overtime": false,
    "priority_drivers": [],
    "fair_rotation": true
  }
}
```

**4. Custom Business Rules**:
```json
{
  "type": "business_rule",
  "parameters": {
    "rule_name": "no_back_to_back_long_routes",
    "condition": "if route_duration > 10 hours",
    "action": "next_day_max_hours = 6",
    "scope": "all_drivers"
  }
}
```

### 11.4 Technical Implementation Strategy

#### 11.4.1 Dynamic Constraint Storage
```sql
-- New table for storing dynamic constraints
CREATE TABLE optimization_constraints (
    constraint_id SERIAL PRIMARY KEY,
    constraint_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL,
    effective_start_date DATE,
    effective_end_date DATE,
    created_by TEXT DEFAULT 'bubblegpt_assistant',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 11.4.2 Constraint Processing Engine
```python
class DynamicConstraintProcessor:
    def __init__(self):
        self.constraint_handlers = {
            'driver_weekly_hours': self.apply_weekly_hour_constraints,
            'route_assignment': self.apply_route_assignment_rules,
            'workload_distribution': self.apply_distribution_rules,
            'business_rule': self.apply_custom_business_rules
        }
    
    async def build_constraints_for_optimization(self, date_range):
        """Dynamically build OR-Tools constraints based on active configuration"""
        active_constraints = await self.get_active_constraints(date_range)
        constraint_set = []
        
        for constraint in active_constraints:
            handler = self.constraint_handlers[constraint.type]
            constraint_set.extend(handler(constraint.parameters))
        
        return constraint_set
```

#### 11.4.3 Natural Language Processing Pipeline
```python
class ConversationalConstraintParser:
    def parse_constraint_request(self, natural_language_input: str) -> Dict:
        """
        Convert natural language to structured constraint definition
        Example: "Set max hours to 40 per week" -> {"type": "driver_weekly_hours", "max_hours": 40}
        """
        # NLP processing to extract:
        # - Constraint type identification
        # - Parameter extraction
        # - Scope determination (all drivers, specific drivers, date ranges)
        # - Validation and error handling
```

### 11.5 User Experience Flow

#### 11.5.1 Conversation Example
```
User: "I want to reduce working hours for all drivers to 40 hours per week"

BubbleGPT Assistant: 
- Parses intent: Modify weekly hour constraint
- Calls: POST /api/v1/assistant/configure-constraints
- Applies new constraint to OR-Tools optimization
- Re-runs optimization with new rules
- Updates Google Sheets
- Confirms: "Weekly hours set to 40h/driver. Re-optimization complete. 38 assignments updated."

User: "Actually, make an exception for driver Thamer, Karl - he can work 45 hours"

BubbleGPT Assistant:
- Parses intent: Add driver-specific exception
- Updates constraint configuration
- Re-optimizes with exception
- Confirms: "Exception added for Thamer, Karl (45h max). Schedule updated."
```

#### 11.5.2 Constraint Management Commands
- **Set Constraints**: "Set maximum daily hours to 10"
- **Add Exceptions**: "Allow Bandzi, Attila to work weekends"
- **Remove Rules**: "Remove the Saturday route restriction"
- **Temporary Changes**: "For this week only, allow 50 hours per driver"
- **View Current Rules**: "Show me all active constraints"
- **Reset to Defaults**: "Reset all constraints to system defaults"

### 11.6 Benefits of Dynamic Constraint System

#### 11.6.1 Operational Flexibility
- **Real-time Adaptation**: Adjust to changing business requirements without code deployment
- **Seasonal Adjustments**: Modify constraints for peak/low seasons
- **Regulatory Compliance**: Quickly implement new labor law requirements
- **Emergency Handling**: Temporary constraint relaxation for urgent situations

#### 11.6.2 User Empowerment
- **Non-technical Configuration**: Business users can modify optimization rules via chat
- **Immediate Feedback**: See constraint effects in Google Sheets within seconds
- **Experimentation**: Try different rules and compare results
- **Historical Tracking**: Maintain audit trail of constraint changes

#### 11.6.3 Business Intelligence Integration
- **Constraint Performance**: Track which constraints improve efficiency
- **Rule Optimization**: Identify most effective constraint combinations
- **Impact Analysis**: Measure before/after effects of constraint changes
- **Compliance Reporting**: Generate reports on constraint adherence

### 11.7 Implementation Phases

#### Phase 1: Basic Dynamic Constraints (Q2 2025)
- Weekly/daily hour limit modification
- Driver-specific exceptions
- Simple route assignment preferences

#### Phase 2: Advanced Rule Engine (Q3 2025)
- Multi-condition business rules
- Temporal constraints (time-based rules)
- Complex dependency handling

#### Phase 3: AI-Assisted Constraint Optimization (Q4 2025)
- Machine learning recommendations for optimal constraints
- Automatic constraint adjustment based on historical performance
- Predictive constraint modeling

#### Phase 4: Full Conversational Optimization (Q1 2026)
- Natural language rule definition
- Voice-based constraint management
- Integrated business intelligence and constraint optimization

This dynamic constraint management system will transform the logistics scheduling platform from a fixed-rule optimization tool into a flexible, conversational business intelligence platform that adapts to changing operational needs in real-time.

This technical documentation provides a complete overview of the current BubbleGPT Assistant workflow and the planned evolution toward dynamic, conversational constraint management.