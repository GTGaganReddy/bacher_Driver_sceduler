# Overview

This is a FastAPI-based logistics driver scheduling backend system that uses OR-Tools optimization to automatically assign drivers to routes based on availability. The system integrates with Google Sheets via Google Cloud Function for automatic schedule updates and uses Supabase PostgreSQL for authentic data persistence. The application optimizes weekly driver schedules for the July 7-13, 2025 period using 21 real drivers and authentic route data, then automatically posts results to Google Sheets via the user's Google Cloud Function.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## August 11, 2025 - Advanced OR-Tools Algorithm with Progressive Hour Consumption
- Updated algorithm with progressive hour consumption using running balance constraints
- Running balance variables track remaining capacity after each chronological date
- Balance constraint: remaining_after_date = remaining_before_date - hours_used_on_date
- Prevents over-assignment through explicit non-negative remaining hours constraints
- More sophisticated hour tracking than simple cumulative constraints
- Maintains Saturday route 452SA assignment to Klagenfurt - Samstagsfahrer
- Pure OR-Tools SCIP solver with advanced mathematical programming techniques

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
- **Pydantic Validation**: Request/response model validation and serialization
- **Dependency Injection**: FastAPI dependencies for service instantiation
- **Error Handling**: Consistent HTTP exception responses

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