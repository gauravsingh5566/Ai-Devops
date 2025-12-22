"""
RAG Service - Local Embeddings
Retrieval-Augmented Generation using Sentence Transformers (LOCAL - NO API CALLS)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import os
import logging
from datetime import datetime
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="RAG Service - Local Embeddings",
    version="3.0.0",
    description="Vector search using Local Sentence Transformers (100% FREE - No API calls)"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Collection names
BEST_PRACTICES_COLLECTION = "aws_best_practices"
INTENT_CACHE_COLLECTION = "cached_intents"

# Local embedding model (384 dimensions, runs locally - NO API calls!)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
SIMILARITY_THRESHOLD = 0.85

# Initialize Qdrant
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    logger.info(f"Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Qdrant: {e}")
    qdrant_client = None

# Initialize local embedding model
logger.info(f"Loading local embedding model: {EMBEDDING_MODEL_NAME}...")
try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info(f"✅ Embedding model loaded! (384D, LOCAL, NO API CALLS)")
except Exception as e:
    logger.error(f"Failed to load embedding model: {e}")
    embedding_model = None


# ============== Pydantic Models ==============

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=5, ge=1, le=20, description="Number of results")

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int

class IntentCacheQuery(BaseModel):
    user_request: str

class CachedIntentResult(BaseModel):
    cached: bool
    intent: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None

class StoreIntentRequest(BaseModel):
    user_request: str
    intent: Dict[str, Any]


# ============== Helper Functions ==============

def get_embedding(text: str) -> List[float]:
    """Generate embedding using LOCAL model (no API call!)"""
    try:
        if not embedding_model:
            raise Exception("Embedding model not loaded")
        
        embedding = embedding_model.encode(text, convert_to_tensor=False)
        embedding_list = embedding.tolist()
        
        if len(embedding_list) != EMBEDDING_DIMENSION:
            raise ValueError(f"Expected {EMBEDDING_DIMENSION}D, got {len(embedding_list)}D")
        
        return embedding_list
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")


def ensure_collection_exists(collection_name: str):
    """Ensure Qdrant collection exists"""
    try:
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            logger.info(f"Creating collection: {collection_name}")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE)
            )
            logger.info(f"Collection created: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to ensure collection exists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== API Endpoints ==============

@app.get("/")
async def root():
    return {
        "service": "RAG Service - Local Embeddings",
        "status": "healthy",
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "embedding_type": "LOCAL (No API calls - 100% FREE)",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    }


@app.post("/search", response_model=SearchResponse)
async def search_best_practices(request: SearchRequest):
    try:
        if not qdrant_client:
            raise HTTPException(status_code=503, detail="Qdrant not available")
        
        ensure_collection_exists(BEST_PRACTICES_COLLECTION)
        query_embedding = get_embedding(request.query)
        
        search_results = qdrant_client.search(
            collection_name=BEST_PRACTICES_COLLECTION,
            query_vector=query_embedding,
            limit=request.limit
        )
        
        results = [
            SearchResult(
                content=result.payload.get('content', ''),
                score=result.score,
                metadata=result.payload.get('metadata', {})
            )
            for result in search_results
        ]
        
        logger.info(f"Search completed: {len(results)} results")
        
        return SearchResponse(results=results, query=request.query, total_results=len(results))
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intent/check-cache", response_model=CachedIntentResult)
async def check_intent_cache(request: IntentCacheQuery):
    try:
        if not qdrant_client:
            raise HTTPException(status_code=503, detail="Qdrant not available")
        
        ensure_collection_exists(INTENT_CACHE_COLLECTION)
        query_embedding = get_embedding(request.user_request)
        
        search_results = qdrant_client.search(
            collection_name=INTENT_CACHE_COLLECTION,
            query_vector=query_embedding,
            limit=1
        )
        
        if search_results and search_results[0].score >= SIMILARITY_THRESHOLD:
            cached_intent = search_results[0].payload.get('intent')
            similarity_score = search_results[0].score
            
            logger.info(f"Cache HIT: similarity={similarity_score:.3f}")
            return CachedIntentResult(cached=True, intent=cached_intent, similarity_score=similarity_score)
        else:
            logger.info("Cache MISS")
            return CachedIntentResult(cached=False)
        
    except Exception as e:
        logger.error(f"Cache check failed: {e}")
        return CachedIntentResult(cached=False)


@app.post("/intent/store")
async def store_intent(request: StoreIntentRequest):
    try:
        if not qdrant_client:
            raise HTTPException(status_code=503, detail="Qdrant not available")
        
        ensure_collection_exists(INTENT_CACHE_COLLECTION)
        embedding = get_embedding(request.user_request)
        point_id = hashlib.md5(request.user_request.encode()).hexdigest()
        
        qdrant_client.upsert(
            collection_name=INTENT_CACHE_COLLECTION,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "user_request": request.user_request,
                    "intent": request.intent,
                    "timestamp": datetime.now().isoformat()
                }
            )]
        )
        
        logger.info(f"Intent cached: {request.user_request[:50]}...")
        return {"status": "success", "message": "Intent cached successfully", "cache_id": point_id}
        
    except Exception as e:
        logger.error(f"Failed to cache intent: {e}")
        return {"status": "warning", "message": f"Failed to cache: {str(e)}"}


@app.get("/intent/stats")
async def get_cache_stats():
    try:
        if not qdrant_client:
            raise HTTPException(status_code=503, detail="Qdrant not available")
        
        try:
            collection_info = qdrant_client.get_collection(INTENT_CACHE_COLLECTION)
            cached_count = collection_info.points_count
        except:
            cached_count = 0
        
        try:
            practices_info = qdrant_client.get_collection(BEST_PRACTICES_COLLECTION)
            practices_count = practices_info.points_count
        except:
            practices_count = 0
        
        return {
            "cached_intents": cached_count,
            "best_practices": practices_count,
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_type": "LOCAL (No API calls)"
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    qdrant_status = "connected" if qdrant_client else "disconnected"
    model_status = "loaded" if embedding_model else "not loaded"
    
    return {
        "status": "healthy",
        "qdrant": qdrant_status,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_status": model_status,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "embedding_type": "LOCAL (No API calls - 100% FREE)",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
