# Overview

This is a FastAPI-based logistics driver scheduling backend system that uses OR-Tools optimization to automatically assign drivers to routes based on availability. The system integrates with Google Sheets via Google Cloud Function for automatic schedule updates and uses Supabase PostgreSQL for authentic data persistence. The application optimizes weekly driver schedules for the July 7-13, 2025 period using 21 real drivers and authentic route data, then automatically posts results to Google Sheets via the user's Google Cloud Function.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## August 22, 2025 - Fixed Assignments Integration Complete and Working
- **✅ INTEGRATION SUCCESS**: Fixed assignments fully operational with `fixed_assignments_count: 36` confirmed in API responses
- **✅ Database issue resolved**: Fixed assignments data successfully inserted into Supabase and accessible by API
- **✅ Optimization verification**: Enhanced OR-Tools optimizer correctly respecting fixed assignments in daily scheduling
- **✅ Actual assignments confirmed**: July 9th and 11th showing correct driver assignments matching fixed constraints
- **✅ End-to-end workflow**: API → Database → Enhanced Optimizer → Fixed Assignments → Google Sheets all working
- **✅ API endpoint operational**: `/api/v1/assistant/optimize-week` functioning properly after router registration fix
- **✅ Enhanced optimizer integration**: OR-Tools with consecutive hours constraints plus fixed assignments working together
- **✅ Database structure**: 36 fixed assignments properly stored with driver_id, route_id, date fields and correct JOINs
- **✅ Production ready**: All 42 routes optimized successfully with fixed assignments constraints applied
- **✅ Google Sheets sync**: Complete driver grid updated with optimized assignments respecting fixed constraints
- **✅ CRUD endpoints complete**: Full fixed assignments management with GET, POST add, and POST delete endpoints
- **✅ Fixed assignments API endpoints**: 
  - `GET /api/v1/assistant/fixed-assignments` - View all fixed assignments
  - `POST /api/v1/assistant/add-fixed-assignment` - Add new fixed assignment
  - `POST /api/v1/assistant/delete-fixed-assignment` - Remove fixed assignment
- **Key drivers with fixed assignments**: Hinteregger Manfred, Rauter Agnes Zita, Niederbichler Daniel, and others across weekdays
- **System architecture**: BubbleGPT → FastAPI Backend → PostgreSQL → Enhanced OR-Tools → Fixed Assignments → Google Sheets

## August 13, 2025 - Complete Technical Documentation with Future Roadmap
- **COMPREHENSIVE DOCUMENTATION**: Created detailed technical documentation for BubbleGPT Assistant workflow
- **Architecture Overview**: BubbleGPT → FastAPI Backend → PostgreSQL → OR-Tools → Google Cloud Function → Google Sheets
- **API Documentation**: All 8 endpoints with request/response formats and internal processing workflows
- **OR-Tools Deep Dive**: Sequential day-by-day optimization algorithm with capacity tracking
- **Database Schema**: Complete PostgreSQL schema with operations and performance characteristics
- **Google Sheets Integration**: Detailed GCF payload format and 147-entry driver grid structure
- **Error Handling & Security**: Comprehensive resilience patterns and authentication flows
- **Deployment Guide**: Cloud Run configuration with environment variables and dependencies
- **FUTURE ROADMAP**: Dynamic constraint management via conversational BubbleGPT interface
- **Flexible Optimization**: Chat-based control of OR-Tools constraints (working hours, route rules, etc.)
- **Implementation Phases**: 4-phase rollout from basic dynamic constraints to full AI-assisted optimization

## August 12, 2025 - Complete Reset Function Enhancement with Auto-Optimization
- **CRITICAL FIX**: Enhanced reset function for complete workflow automation
- **Full data reset**: Clears assignments, routes, and resets driver availability consistently
- **Auto-optimization**: Automatically runs OR-Tools optimization after database reset
- **Google Sheets sync**: Updates sheets with optimized reset state via Google Cloud Function
- **Smart route preservation**: Only removes manually added routes while keeping original system data
- **Complete workflow**: Reset → Optimize → Update Sheets in single operation

## August 12, 2025 - Complete Deployment Fix & Health Check Enhancement
- **CRITICAL DEPLOYMENT FIX**: Applied all suggested fixes for Cloud Run deployment failures
- **Fixed run command**: Explicitly handles main.py execution with proper port binding on 5000
- **Enhanced root endpoint**: Added database connectivity check and comprehensive API info
- **Multiple health endpoints**: Added `/healthz`, `/ready`, `/live` for different deployment health checks
- **Production configuration**: Deployment-aware uvicorn settings with optimized logging
- **Environment detection**: Added Cloud Run and deployment environment detection in settings
- **Port binding fix**: Always uses PORT environment variable (set by Cloud Run) with 0.0.0.0 binding
- **Error handling**: Robust exception handling in health checks to prevent deployment failures
- **Production optimizations**: Disabled reload, added access logs, and single worker for Cloud Run
- **Deployment ready**: All three main issues resolved - run command, port configuration, health checks

## August 12, 2025 - Complete OpenAI Assistant Integration with 422 Error Resolution
- **CRITICAL FIX**: Resolved all 422 request format errors for OpenAI Assistant integration
- Added simplified endpoints: `/update-driver-availability` and `/add-single-route`
- Both user request formats now work perfectly (driver availability + route addition)
- Comprehensive OpenAI Assistant action code with full API integration  
- Implemented system reset endpoint for clearing assignments and resetting availability
- Created complete natural language interface for all scheduling operations
- F entry functionality fully operational (unavailable drivers show as route="F")
- Built comprehensive setup documentation and demo scripts
- All six Assistant API endpoints now fully operational with simplified request formats
- Complete data flow verified: API requests → OR-Tools optimization → Google Sheets export
- 46 total routes successfully managed with dynamic assignment optimization

## August 11, 2025 - Sequential OR-Tools Algorithm Implementation
- Replaced progressive algorithm with true sequential optimization approach
- Day-by-day chronological processing: solves each date independently in order
- Dynamic capacity tracking: updates remaining driver hours between each day's optimization
- Multiple solver instances: creates fresh SCIP solver for each day's route assignments
- Real-time hour consumption: capacity reduces after each assignment for subsequent days
- More realistic modeling: mirrors actual schedule building process (day-by-day)
- Maintains Saturday route 452SA assignment to Klagenfurt - Samstagsfahrer
- Pure OR-Tools SCIP solver with sequential mathematical programming approach

# System Architecture

## Backend Framework
- **FastAPI**: RESTful API framework with automatic OpenAPI documentation
- **Async/Await Pattern**: Full asynchronous architecture for database and external service calls
- **Modular Router Structure**: Organized endpoints by domain (drivers, routes, scheduling, health)

## Data Layer
- **PostgreSQL Database**: Primary data store hosted on Supabase
- **Connection Pooling**: AsyncPG connection pool for efficient database connections
- **Schema Design**: Four main tables - drivers, driver_availability, routes, and assignments
- **Service Layer Pattern**: DatabaseService abstracts database operations from API endpoints

## Optimization Engine
- **OR-Tools CP-SAT Solver**: Google's constraint programming solver for optimal driver-route assignments
- **Multi-constraint Optimization**: Considers driver availability, route requirements, and scheduling preferences
- **Weekly Scheduling**: Generates optimized assignments for 7-day periods

## External Integrations
- **Google Sheets Integration**: Updates external spreadsheets via Google Cloud Function HTTP endpoint
- **RESTful Communication**: JSON-based data exchange with external services

## Configuration Management
- **Pydantic Settings**: Type-safe environment variable management
- **Environment-based Config**: Separate settings for database, Google Cloud Function, and application parameters

## API Design
- **RESTful Endpoints**: Standard HTTP methods for CRUD operations
- **Dual Request Formats**: Both simplified and advanced endpoints for OpenAI Assistant integration
- **Pydantic Validation**: Request/response model validation and serialization
- **Dependency Injection**: FastAPI dependencies for service instantiation
- **Error Handling**: Consistent HTTP exception responses
- **OpenAI Assistant Ready**: Six endpoints with proper request/response formats

## Application Lifecycle
- **Startup/Shutdown Hooks**: Manages database connection pool lifecycle
- **Health Checks**: Database and service health monitoring endpoints
- **Structured Logging**: Comprehensive logging with configurable levels

# External Dependencies

## Database Services
- **Supabase PostgreSQL**: Cloud-hosted PostgreSQL database with connection pooling
- **AsyncPG**: Async PostgreSQL driver for Python

## Optimization Libraries
- **OR-Tools**: Google's optimization tools for constraint programming and scheduling

## External APIs
- **Google Cloud Function**: HTTP endpoint for updating Google Sheets with scheduling data
- **HTTPX**: Async HTTP client for external API calls

## Core Libraries
- **FastAPI**: Web framework with OpenAPI support
- **Pydantic**: Data validation and settings management
- **Python Logging**: Built-in logging system with custom configuration

## Development Tools
- **Environment Variables**: Configuration through .env files
- **Type Hints**: Full type annotation support throughout codebase