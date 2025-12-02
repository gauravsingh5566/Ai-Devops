#!/usr/bin/env python3
"""
Startup script for MCP Service
Handles initialization, validation, and starts the FastAPI server
"""

import sys
import os


def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import fastapi
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
    print("🚀 Starting MCP Service...")
    print("=" * 50)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies OK")
    
    # Import and start the app
    print("⚡ Loading MCP Service application...")
    try:
        import uvicorn
        from main import app
        
        print("✅ Application loaded successfully")
        print("=" * 50)
        print("🎯 MCP Service is starting on http://0.0.0.0:8003")
        print("📚 API Docs available at http://0.0.0.0:8003/docs")
        print("💡 Validation endpoint: POST /validate")
        print("=" * 50)
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8003,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
