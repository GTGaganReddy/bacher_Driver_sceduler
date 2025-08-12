# Overview

This is a FastAPI-based logistics driver scheduling backend system that uses OR-Tools optimization to automatically assign drivers to routes based on availability. The system integrates with Google Sheets via Google Cloud Function for automatic schedule updates and uses Supabase PostgreSQL for authentic data persistence. The application optimizes weekly driver schedules for the July 7-13, 2025 period using 21 real drivers and authentic route data, then automatically posts results to Google Sheets via the user's Google Cloud Function.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## August 12, 2025 - Reset Function Fix & Data Consistency Enhancement
- **CRITICAL FIX**: Fixed reset function to properly clear both routes and driver availability
- **Route reset logic**: Now removes manually added routes while preserving original system data
- **Consistent state management**: Reset function maintains data integrity across all tables
- **Timestamp-based filtering**: Only clears routes added after initial system setup
- **Complete reset workflow**: Assignments, routes, and availability all reset consistently

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