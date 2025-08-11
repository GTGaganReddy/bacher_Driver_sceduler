# OR-Tools Input Data Format Specification

## Current Database Schema vs OR-Tools Expected Format

### 1. DRIVERS Data

**Database Output:**
```python
{
    "driver_id": 14,
    "name": "Bandzi, Attila", 
    "details": '{"type": "full_time", "monthly_hours": "174:00"}',  # JSON string
    "created_at": datetime.datetime(...),
    "monthly_hours_limit": 174  # May or may not exist
}
```

**OR-Tools Expected Input:**
```python
{
    "driver_id": 14,
    "name": "Bandzi, Attila",
    "monthly_hours_limit": 174.0,  # Must be float
    "details": {  # Optional - if present, should be dict not string
        "type": "full_time",
        "monthly_hours": "174:00"
    }
}
```

### 2. ROUTES Data

**Database Output:**
```python
{
    "route_id": 1,
    "date": datetime.date(2025, 7, 7),
    "route_name": "431oS",
    "details": '{"type": "weekday", "duration": "11:00", "route_code": "431oS"}',  # JSON string
    "day_of_week": "monday",
    "created_at": datetime.datetime(...)
}
```

**OR-Tools Expected Input:**
```python
{
    "route_id": 1,
    "date": datetime.date(2025, 7, 7),  # OR date string "2025-07-07"
    "route_name": "431oS",
    "details": {  # Must be dict, not string
        "type": "weekday",
        "duration": "11:00",  # Will be parsed to 11.0 hours
        "route_code": "431oS"
    }
}
```

### 3. AVAILABILITY Data

**Database Output:**
```python
{
    "id": 14,
    "driver_id": 14,
    "date": datetime.date(2025, 7, 7),
    "available": True,
    "available_hours": Decimal('8.00'),  # Decimal type
    "shift_preference": "any",
    "max_routes": 2,
    "notes": "Available - can be edited via API",
    "created_at": datetime.datetime(...),
    "updated_at": datetime.datetime(...),
    "name": "Bandzi, Attila"  # Joined from drivers table
}
```

**OR-Tools Expected Input:**
```python
{
    "driver_id": 14,
    "date": datetime.date(2025, 7, 7),  # OR date string "2025-07-07"
    "available": True,
    "available_hours": 8.0,  # Must be float, not Decimal
    "max_routes": 2,
    "shift_preference": "any"
}
```

## Key Conversion Requirements

1. **JSON String Parsing**: Database `details` fields are JSON strings that need parsing to dicts
2. **Decimal to Float**: Database Decimal types must convert to float
3. **Date Handling**: Both datetime.date objects and ISO strings work
4. **Duration Parsing**: "11:00" format needs conversion to 11.0 float hours
5. **Field Filtering**: Extra database fields (id, created_at, etc.) should be ignored

## Current OR-Tools Algorithm Constraints

- **Available Hours**: Currently overridden to 16.0 if database value < 12.0
- **Max Routes**: Currently overridden to 2 if database value < 2
- **Route Duration**: Parsed from details.duration field
- **Monthly Hours**: Defaults to 174.0 if not found

## Critical Data Points from July 7-13, 2025

- **42 total routes** (8 per weekday, 2 Saturday)
- **21 drivers** available
- **147 availability records** 
- **Route durations**: Mix of 8:00 and 11:00 hour routes
- **Saturday routes**: 2 special routes on 2025-07-12