"""Database models and schemas for the driver scheduling backend."""

# This file contains database schema definitions and helper functions
# The actual table creation is handled in connection.py

# Table schemas for reference:

# drivers table:
# - driver_id: SERIAL PRIMARY KEY
# - name: TEXT NOT NULL
# - created_at: TIMESTAMP DEFAULT NOW()

# driver_availability table:
# - id: SERIAL PRIMARY KEY
# - driver_id: INT REFERENCES drivers(driver_id) ON DELETE CASCADE
# - date: DATE NOT NULL
# - available: BOOLEAN NOT NULL DEFAULT TRUE
# - created_at: TIMESTAMP DEFAULT NOW()
# - UNIQUE(driver_id, date)

# routes table:
# - route_id: SERIAL PRIMARY KEY
# - date: DATE NOT NULL
# - route_name: TEXT NOT NULL
# - details: JSONB
# - created_at: TIMESTAMP DEFAULT NOW()

# assignments table:
# - id: SERIAL PRIMARY KEY
# - week_start: DATE NOT NULL
# - assignments: JSONB NOT NULL
# - created_at: TIMESTAMP DEFAULT NOW()

# fixed_driver_routes table:
# - id: SERIAL PRIMARY KEY
# - driver_id: INT REFERENCES drivers(driver_id) ON DELETE CASCADE
# - route_pattern: VARCHAR(50) NOT NULL (e.g., '452SA', '431oS')
# - priority: INT DEFAULT 1 (1 = highest priority fixed assignment)
# - day_of_week: VARCHAR(20) ('monday', 'tuesday', etc. or 'any')
# - effective_start_date: DATE (when assignment becomes effective)
# - effective_end_date: DATE (when assignment expires, NULL = permanent)
# - is_active: BOOLEAN DEFAULT TRUE
# - notes: TEXT (business reason for fixed assignment)
# - created_at: TIMESTAMP DEFAULT NOW()
# - updated_at: TIMESTAMP DEFAULT NOW()
