"""
MongoDB Database Configuration and Utilities
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from enum import Enum

# MongoDB connection string
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://devops:devops123@mongodb:27017/devops?authSource=admin')

# Collections enum
class Collections:
    USERS = 'users'
    PROJECTS = 'projects'
    BUILD_JOBS = 'build_jobs'
    DEPLOYMENTS = 'deployments'
    SECURITY_SCANS = 'security_scans'
    TEST_RESULTS = 'test_results'
    AGENTS = 'agents'

class MongoDB:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB (async)"""
        if not self.client:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client.get_default_database()
            print(f"✅ Connected to MongoDB: {self.db.name}")
        return self.db
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("Disconnected from MongoDB")
    
    def get_sync_client(self):
        """Get synchronous MongoDB client"""
        client = MongoClient(MONGODB_URL)
        return client.get_default_database()


# Global MongoDB instance
mongodb = MongoDB()


async def get_collection(collection_name: str):
    """
    Get a MongoDB collection
    
    Args:
        collection_name: Name of the collection or Collections enum value
        
    Returns:
        MongoDB collection object
    """
    db = await mongodb.connect()
    
    # Handle enum or string
    if isinstance(collection_name, Collections):
        collection_name = collection_name.value
    
    return db[collection_name]


# Helper functions
async def ensure_indexes():
    """Create indexes for better query performance"""
    db = await mongodb.connect()
    
    # Users collection indexes
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("github.username")
    
    # Projects collection indexes
    await db.projects.create_index([("user_id", 1), ("full_name", 1)])
    await db.projects.create_index("source")
    await db.projects.create_index("imported_at")
    
    # Build jobs collection indexes
    await db.build_jobs.create_index("job_id", unique=True)
    await db.build_jobs.create_index([("user_id", 1), ("created_at", -1)])
    await db.build_jobs.create_index("status")
    
    print("✅ MongoDB indexes created")


if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test connection
        db = await mongodb.connect()
        print(f"Connected to database: {db.name}")
        
        # Test collection access
        users = await get_collection(Collections.USERS)
        print(f"Users collection: {users.name}")
        
        # Create indexes
        await ensure_indexes()
        
        await mongodb.disconnect()
    
    asyncio.run(test())
