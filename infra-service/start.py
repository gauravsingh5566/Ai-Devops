#!/usr/bin/env python3
"""
Startup script for Infrastructure Service
Handles initialization, validation, and starts the FastAPI server
"""

import sys
import os
import subprocess
from pathlib import Path


def check_terraform():
    """Check if Terraform is installed"""
    try:
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Terraform found: {version}")
            return True
        else:
            print("❌ ERROR: Terraform not working properly")
            return False
            
    except FileNotFoundError:
        print("❌ ERROR: Terraform not installed")
        print("\nPlease install Terraform:")
        print("  https://www.terraform.io/downloads")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to check Terraform: {e}")
        return False


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


def setup_workspace_directory():
    """Create workspace directory"""
    workspace_dir = os.getenv("WORKSPACE_DIR", "/app/workspaces")
    
    try:
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Workspace directory ready: {workspace_dir}")
        return True
    except Exception as e:
        print(f"❌ ERROR: Could not create workspace directory: {e}")
        return False


def main():
    """Main startup function"""
    print("🚀 Starting Infrastructure Service...")
    print("=" * 50)
    
    # Check Terraform
    print("🔧 Checking Terraform installation...")
    if not check_terraform():
        print("\n⚠️  WARNING: Terraform not found. Install it to enable deployments.")
        print("Service will start but deployments will fail.")
    
    # Check dependencies
    print("📦 Checking Python dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies OK")
    
    # Setup workspace
    print("📁 Setting up workspace directory...")
    setup_workspace_directory()
    
    # Import and start the app
    print("🏗️  Loading Infrastructure Service application...")
    try:
        import uvicorn
        from main import app
        
        print("✅ Application loaded successfully")
        print("=" * 50)
        print("🎯 Infrastructure Service is starting on http://0.0.0.0:8004")
        print("📚 API Docs available at http://0.0.0.0:8004/docs")
        print("💡 Create deployment: POST /deployments")
        print("=" * 50)
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8004,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
