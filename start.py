#!/usr/bin/env python3
"""
Cloud Run optimized startup script
Handles deployment-specific configuration and error handling
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging before importing anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_deployment_environment():
    """Setup environment for Cloud Run deployment"""
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Environment checks
    port = os.getenv("PORT")
    if port:
        logger.info(f"Cloud Run detected - PORT: {port}")
        os.environ["IS_DEPLOYMENT"] = "true"
    else:
        logger.info("Development environment detected")
        os.environ["PORT"] = "5000"
    
    # Critical environment variables check
    if not os.getenv("DATABASE_URL"):
        logger.error("DATABASE_URL not found - deployment will fail")
        sys.exit(1)
    else:
        logger.info("DATABASE_URL configured")

def main():
    """Main startup function"""
    try:
        logger.info("Starting Driver Scheduling Backend for deployment...")
        
        # Setup deployment environment
        setup_deployment_environment()
        
        # Import and run the FastAPI app
        import uvicorn
        from main import app
        
        # Cloud Run optimized configuration
        port = int(os.getenv("PORT", 5000))
        
        config = {
            "host": "0.0.0.0",
            "port": port,
            "workers": 1,
            "timeout_keep_alive": 120,
            "timeout_graceful_shutdown": 30,
            "log_level": "info",
            "access_log": True,
            "use_colors": False,
        }
        
        logger.info(f"Starting server with config: {config}")
        uvicorn.run(app, **config)
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()