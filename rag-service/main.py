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
from terraform_store import create_terraform_store
from template_store import create_template_store
from infra_templates import INFRASTRUCTURE_TEMPLATES, get_template_text_for_embedding

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

# Initialize Terraform code store
terraform_store = None
if qdrant_client and embedding_model:
    try:
        terraform_store = create_terraform_store(qdrant_client, embedding_model)
        logger.info("✅ Terraform code store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Terraform store: {e}")

# Initialize Infrastructure Template store
template_store = None
if qdrant_client and embedding_model:
    try:
        template_store = create_template_store(qdrant_client, embedding_model)
        logger.info("✅ Infrastructure template store initialized")
        
        # Load pre-defined templates on startup
        logger.info("Loading pre-defined infrastructure templates...")
        for template in INFRASTRUCTURE_TEMPLATES:
            template_store.store_template(template)
        logger.info(f"✅ Loaded {len(INFRASTRUCTURE_TEMPLATES)} infrastructure templates")
    except Exception as e:
        logger.error(f"Failed to initialize template store: {e}")


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

class StoreTerraformRequest(BaseModel):
    terraform_code: str
    deployment_id: str
    resource_types: List[str]
    description: str
    metadata: Optional[Dict[str, Any]] = {}

class SearchTerraformRequest(BaseModel):
    error_description: str
    failed_code: str
    resource_types: List[str]
    top_k: int = Field(default=3, ge=1, le=10)

class TerraformExample(BaseModel):
    terraform_code: str
    description: str
    resource_types: List[str]
    similarity_score: Optional[float] = None
    deployment_id: str
    metadata: Dict[str, Any] = {}

class SearchTemplateRequest(BaseModel):
    user_requirement: str
    top_k: int = Field(default=3, ge=1, le=5)

class InfrastructureTemplate(BaseModel):
    template_id: str
    name: str
    description: str
    use_case: str
    components: List[str]
    services: Dict[str, List[str]]
    estimated_cost: str
    complexity: str
    tags: List[str]
    similarity_score: Optional[float] = None


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


@app.post("/terraform/store")
async def store_terraform_example(request: StoreTerraformRequest):
    """
    Store successful Terraform deployment for future reference
    """
    if not terraform_store:
        raise HTTPException(status_code=503, detail="Terraform store not available")
    
    try:
        success = terraform_store.store_successful_terraform(
            terraform_code=request.terraform_code,
            deployment_id=request.deployment_id,
            resource_types=request.resource_types,
            description=request.description,
            metadata=request.metadata
        )
        
        if success:
            return {
                "status": "stored",
                "deployment_id": request.deployment_id,
                "message": "Terraform code stored successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store Terraform code")
            
    except Exception as e:
        logger.error(f"Error storing Terraform: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/terraform/search", response_model=List[TerraformExample])
async def search_terraform_examples(request: SearchTerraformRequest):
    """
    Search for similar working Terraform examples to help fix errors
    """
    if not terraform_store:
        raise HTTPException(status_code=503, detail="Terraform store not available")
    
    try:
        examples = terraform_store.search_similar_terraform(
            error_description=request.error_description,
            failed_code=request.failed_code,
            resource_types=request.resource_types,
            top_k=request.top_k
        )
        
        return examples
        
    except Exception as e:
        logger.error(f"Error searching Terraform: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/terraform/stats")
async def get_terraform_stats():
    """Get statistics about stored Terraform examples"""
    if not terraform_store:
        raise HTTPException(status_code=503, detail="Terraform store not available")
    
    try:
        collection_info = qdrant_client.get_collection("terraform_examples")
        return {
            "total_examples": collection_info.points_count,
            "status": "active"
        }
    except Exception as e:
        return {
            "total_examples": 0,
            "status": "empty or not initialized"
        }


@app.post("/templates/search", response_model=List[InfrastructureTemplate])
async def search_infrastructure_templates(request: SearchTemplateRequest):
    """
    Search for matching infrastructure templates based on user requirements
    """
    if not template_store:
        raise HTTPException(status_code=503, detail="Template store not available")
    
    try:
        templates = template_store.search_templates(
            user_requirement=request.user_requirement,
            top_k=request.top_k
        )
        
        return templates
        
    except Exception as e:
        logger.error(f"Error searching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates/all", response_model=List[Dict])
async def get_all_templates():
    """Get all available infrastructure templates"""
    if not template_store:
        raise HTTPException(status_code=503, detail="Template store not available")
    
    try:
        templates = template_store.get_all_templates()
        return templates
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates/stats")
async def get_template_stats():
    """Get template collection statistics"""
    if not template_store:
        raise HTTPException(status_code=503, detail="Template store not available")
    
    try:
        collection_info = qdrant_client.get_collection("infrastructure_templates")
        return {
            "total_templates": collection_info.points_count,
            "predefined_templates": len(INFRASTRUCTURE_TEMPLATES),
            "status": "active"
        }
    except Exception as e:
        return {
            "total_templates": 0,
            "predefined_templates": len(INFRASTRUCTURE_TEMPLATES),
            "status": "not initialized"
        }


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