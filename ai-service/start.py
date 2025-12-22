#!/usr/bin/env python3
"""
Startup script for AI Service
Handles initialization, validation, and starts the FastAPI server
"""

import sys
import os
from pathlib import Path

def check_environment():
    """Validate required environment variables"""
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"  export {var}=your-value")
        print("\nOr use Docker:")
        print("  docker run -e GEMINI_API_KEY=your-key -p 8001:8001 ai-service")
        return False
    
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import google.generativeai
        import pydantic
        import uvicorn
        return True
    except ImportError as e:
        print(f"❌ ERROR: Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting AI Service...")
    print("=" * 50)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies OK")
    
    # Check environment
    print("🔐 Checking environment variables...")
    if not check_environment():
        sys.exit(1)
    print("✅ Environment OK")
    
    # Import and start the app
    print("🧠 Loading AI Service application...")
    try:
        import uvicorn
        from main import app
        
        print("✅ Application loaded successfully")
        print("=" * 50)
        print("🎯 AI Service is starting on http://0.0.0.0:8001")
        print("📚 API Docs available at http://0.0.0.0:8001/docs")
        print("=" * 50)
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()