#!/usr/bin/env python3
"""
Startup script for RAG Service
Handles initialization, validation, and starts the FastAPI server
"""

import sys
import os
from pathlib import Path


def check_environment():
    """Validate required environment variables"""
    # No API key needed - using local embeddings!
    print("✅ Using local embeddings - no API key required")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import fastapi
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient
        import pydantic
        import uvicorn
        return True
    except ImportError as e:
        print(f"❌ ERROR: Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def setup_data_directory():
    """Check Qdrant connection"""
    import os
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = os.getenv("QDRANT_PORT", "6333")
    
    print(f"📡 Qdrant configured at: {qdrant_host}:{qdrant_port}")
    return True


def main():
    """Main startup function"""
    print("🚀 Starting RAG Service...")
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
    
    # Setup data directory
    print("📡 Checking Qdrant configuration...")
    setup_data_directory()
    
    # Import and start the app
    print("📚 Loading RAG Service application...")
    try:
        import uvicorn
        from main import app
        
        print("✅ Application loaded successfully")
        print("=" * 50)
        print("🎯 RAG Service is starting on http://0.0.0.0:8002")
        print("📚 API Docs available at http://0.0.0.0:8002/docs")
        print("💡 Seed knowledge base: POST /seed")
        print("=" * 50)
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8002,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()