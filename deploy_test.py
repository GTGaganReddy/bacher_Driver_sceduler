#!/usr/bin/env python3
"""
Deployment Test Script
Tests critical components needed for successful deployment
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime

async def test_deployment():
    """Test deployment readiness"""
    print("=== DEPLOYMENT READINESS TEST ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Environment variables:")
    print(f"  PORT: {os.getenv('PORT', 'NOT_SET')}")
    print(f"  DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT_SET'}")
    print(f"  K_SERVICE: {os.getenv('K_SERVICE', 'NOT_SET')}")
    print(f"  CLOUD_RUN_SERVICE: {os.getenv('CLOUD_RUN_SERVICE', 'NOT_SET')}")
    
    # Test database connection
    print("\n=== DATABASE CONNECTION TEST ===")
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found")
            return False
        
        print("✅ DATABASE_URL found")
        conn = await asyncpg.connect(database_url)
        
        # Simple test query
        result = await conn.fetchval("SELECT 1 as test")
        await conn.close()
        
        if result == 1:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed - unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Test imports
    print("\n=== IMPORT TEST ===")
    try:
        import fastapi
        import uvicorn
        import ortools
        import pydantic
        import httpx
        print("✅ All critical imports successful")
        
        print(f"  FastAPI: {fastapi.__version__}")
        print(f"  Uvicorn: {uvicorn.__version__}")
        print(f"  OR-Tools: {ortools.__version__}")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test FastAPI app creation
    print("\n=== FASTAPI APP TEST ===")
    try:
        from main import app
        print("✅ FastAPI app created successfully")
        
        # Test root endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/")
        
        if response.status_code == 200:
            print("✅ Root endpoint responds")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FastAPI app test failed: {e}")
        return False
    
    print("\n=== DEPLOYMENT TEST RESULT ===")
    print("✅ ALL TESTS PASSED - Ready for deployment")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_deployment())
    sys.exit(0 if result else 1)