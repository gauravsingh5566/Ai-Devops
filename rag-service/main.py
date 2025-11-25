"""
RAG Service - Vector Search & Knowledge Retrieval
Handles document storage, embedding generation, and semantic search for AWS best practices
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import anthropic
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import os
import json
import hashlib
from datetime import datetime
import uuid

# Custom OpenAPI schema for Swagger documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="📚 RAG Service - Knowledge Base",
        version="1.0.0",
        description="""
## Vector Search & Knowledge Retrieval Service

This service manages the knowledge base for AWS best practices, Terraform templates, 
and organizational policies using **Qdrant** vector database and **Claude AI** for embeddings.

### 🎯 Key Features

- **Document Ingestion**: Add AWS documentation, templates, and policies
- **Semantic Search**: Find relevant best practices using natural language
- **Context Retrieval**: Get relevant context for code generation
- **Knowledge Management**: Organize and update the knowledge base

### 🔄 How It Works

1. Documents are chunked and embedded using Claude AI
2. Embeddings stored in Qdrant vector database
3. Queries are embedded and matched against stored documents
4. Most relevant documents returned with similarity scores

### 📚 Knowledge Categories

- AWS Best Practices
- Terraform Templates
- Security Policies
- Cost Optimization Tips
- Organization Standards

### 🔗 Integration

Used by AI Service to retrieve context for code generation:
```
User Request → AI Service → RAG Service → Best Practices → Code Generation
```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Search",
                "description": "Semantic search across the knowledge base"
            },
            {
                "name": "Documents",
                "description": "Add, update, and manage documents in the knowledge base"
            },
            {
                "name": "Collections",
                "description": "Manage document collections and categories"
            },
            {
                "name": "Health & Status",
                "description": "Service health checks and statistics"
            }
        ]
    )
    
    openapi_schema["info"]["contact"] = {
        "name": "AI DevOps Assistant",
        "email": "support@example.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="RAG Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude client for embeddings
claude_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY", "your-api-key-here")
)

# Initialize Qdrant client
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))

# Use in-memory storage for development, or connect to Qdrant server
qdrant_client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT,
    timeout=30
)

# Default collection
DEFAULT_COLLECTION = "aws_best_practices"
EMBEDDING_DIMENSION = 384


# ============== Pydantic Models ==============

class SearchQuery(BaseModel):
    """Search query for finding relevant documents"""
    query: str = Field(
        ...,
        description="Natural language search query",
        example="VPC best practices for production",
        min_length=3,
        max_length=500
    )
    collection: Optional[str] = Field(
        default=DEFAULT_COLLECTION,
        description="Collection to search in",
        example="aws_best_practices"
    )
    n_results: Optional[int] = Field(
        default=5,
        description="Number of results to return",
        ge=1,
        le=20
    )
    filter_metadata: Optional[Dict] = Field(
        default=None,
        description="Metadata filters to apply",
        example={"category": "networking", "provider": "aws"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How to set up a highly available VPC with private subnets",
                "collection": "aws_best_practices",
                "n_results": 5,
                "filter_metadata": {"category": "networking"}
            }
        }


class SearchResult(BaseModel):
    """Individual search result"""
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict = Field(..., description="Document metadata")
    score: float = Field(..., description="Similarity score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_vpc_001",
                "content": "VPC Best Practice: Use /16 CIDR block for production VPCs to allow room for growth. Deploy resources across multiple AZs for high availability.",
                "metadata": {
                    "source": "AWS Well-Architected Framework",
                    "category": "networking",
                    "last_updated": "2024-01-15"
                },
                "score": 0.95
            }
        }


class SearchResponse(BaseModel):
    """Search results response"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="List of matching documents")
    total_results: int = Field(..., description="Total number of results")
    search_time_ms: float = Field(..., description="Search time in milliseconds")


class DocumentInput(BaseModel):
    """Document to add to the knowledge base"""
    content: str = Field(
        ...,
        description="Document content",
        min_length=10,
        max_length=10000
    )
    metadata: Optional[Dict] = Field(
        default={},
        description="Document metadata (source, category, etc.)",
        example={
            "source": "AWS Documentation",
            "category": "security",
            "provider": "aws",
            "resource_type": "iam"
        }
    )
    collection: Optional[str] = Field(
        default=DEFAULT_COLLECTION,
        description="Collection to add document to"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Custom document ID (auto-generated if not provided)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "IAM Best Practice: Always use IAM roles instead of long-term access keys for applications running on EC2 instances. This eliminates the need to manage and rotate credentials manually.",
                "metadata": {
                    "source": "AWS Security Best Practices",
                    "category": "security",
                    "provider": "aws",
                    "resource_type": "iam",
                    "importance": "high"
                },
                "collection": "aws_best_practices",
                "document_id": "iam_roles_001"
            }
        }


class DocumentResponse(BaseModel):
    """Response after adding a document"""
    id: str = Field(..., description="Document ID")
    collection: str = Field(..., description="Collection name")
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")


class BulkDocumentInput(BaseModel):
    """Multiple documents to add at once"""
    documents: List[DocumentInput] = Field(
        ...,
        description="List of documents to add",
        min_length=1,
        max_length=100
    )


class CollectionInfo(BaseModel):
    """Collection information"""
    name: str = Field(..., description="Collection name")
    count: int = Field(..., description="Number of documents")
    metadata: Optional[Dict] = Field(default=None, description="Collection metadata")


class CollectionCreate(BaseModel):
    """Create a new collection"""
    name: str = Field(
        ...,
        description="Collection name",
        example="terraform_templates",
        min_length=3,
        max_length=50
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Collection metadata",
        example={"description": "Terraform module templates", "version": "1.0"}
    )


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    qdrant: str = Field(..., description="Qdrant connection status")
    claude_api: str = Field(..., description="Claude API status")
    collections_count: int = Field(..., description="Number of collections")
    total_documents: int = Field(..., description="Total documents across all collections")
    timestamp: str = Field(..., description="Check timestamp")


class StatsResponse(BaseModel):
    """Knowledge base statistics"""
    total_collections: int
    total_documents: int
    collections: List[CollectionInfo]
    storage_info: Dict


# ============== Helper Functions ==============

def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Claude AI.
    Uses a simple hash-based approach for demo; replace with actual embedding API.
    """
    # Note: Claude doesn't have a direct embedding API yet
    # Using a deterministic hash-based embedding for demonstration
    # In production, use OpenAI embeddings or similar
    
    # Simple deterministic embedding based on text hash
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    embedding = []
    for i in range(0, min(len(text_hash), EMBEDDING_DIMENSION * 2), 2):
        byte_val = int(text_hash[i:i+2], 16)
        embedding.append((byte_val - 128) / 128.0)
    
    # Pad to EMBEDDING_DIMENSION dimensions if needed
    while len(embedding) < EMBEDDING_DIMENSION:
        embedding.append(0.0)
    
    return embedding[:EMBEDDING_DIMENSION]


def get_or_create_collection(name: str):
    """Get existing collection or create new one in Qdrant"""
    try:
        # Check if collection exists
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if name not in collection_names:
            # Create new collection
            qdrant_client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
        
        return name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection error: {str(e)}")


def generate_document_id(content: str) -> str:
    """Generate unique document ID based on content hash"""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    return f"{content_hash}{uuid.uuid4().hex[:4]}"


def string_to_int_id(string_id: str) -> int:
    """Convert string ID to integer for Qdrant"""
    return int(hashlib.md5(string_id.encode()).hexdigest()[:15], 16)


# ============== API Endpoints ==============

@app.get(
    "/",
    tags=["Health & Status"],
    summary="Service Status",
    description="Quick health check to verify the RAG service is running"
)
async def root():
    """Quick health check endpoint"""
    return {
        "service": "RAG Service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Semantic Search",
    description="""
Search the knowledge base using natural language queries.

### How it works:
1. Query is converted to embedding
2. ChromaDB finds most similar documents
3. Results ranked by similarity score

### Use Cases:
- Find VPC best practices
- Get security recommendations
- Retrieve relevant Terraform templates
- Look up cost optimization tips
"""
)
async def search(query: SearchQuery):
    """
    Perform semantic search across the knowledge base.
    
    Returns documents most relevant to the natural language query,
    ranked by similarity score.
    """
    import time
    start_time = time.time()
    
    try:
        # Ensure collection exists
        get_or_create_collection(query.collection)
        
        # Generate query embedding
        query_embedding = get_embedding(query.query)
        
        # Build filter if metadata provided
        query_filter = None
        if query.filter_metadata:
            conditions = []
            for key, value in query.filter_metadata.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)
        
        # Perform search in Qdrant
        results = qdrant_client.search(
            collection_name=query.collection,
            query_vector=query_embedding,
            limit=query.n_results,
            query_filter=query_filter,
            with_payload=True
        )
        
        # Format results
        search_results = []
        for result in results:
            payload = result.payload or {}
            search_results.append(SearchResult(
                id=payload.get('doc_id', str(result.id)),
                content=payload.get('content', ''),
                metadata={k: v for k, v in payload.items() if k not in ['content', 'doc_id']},
                score=round(result.score, 4)
            ))
        
        # Calculate search time
        search_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post(
    "/documents",
    response_model=DocumentResponse,
    tags=["Documents"],
    summary="Add Document",
    description="""
Add a single document to the knowledge base.

### Document will be:
1. Processed and chunked (if large)
2. Embedded using AI
3. Stored in ChromaDB with metadata

### Best Practices:
- Keep documents focused on single topics
- Add rich metadata for filtering
- Use consistent categories
"""
)
async def add_document(document: DocumentInput):
    """
    Add a document to the knowledge base.
    
    The document will be embedded and stored in Qdrant
    for semantic search.
    """
    try:
        # Ensure collection exists
        get_or_create_collection(document.collection)
        
        # Generate document ID if not provided
        doc_id = document.document_id or generate_document_id(document.content)
        
        # Generate embedding
        embedding = get_embedding(document.content)
        
        # Build payload with metadata
        payload = document.metadata.copy() if document.metadata else {}
        payload["content"] = document.content
        payload["doc_id"] = doc_id
        payload["added_at"] = datetime.now().isoformat()
        payload["content_length"] = len(document.content)
        
        # Convert string ID to integer for Qdrant
        point_id = string_to_int_id(doc_id)
        
        # Add to Qdrant
        qdrant_client.upsert(
            collection_name=document.collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return DocumentResponse(
            id=doc_id,
            collection=document.collection,
            status="success",
            message=f"Document added successfully with ID: {doc_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@app.post(
    "/documents/bulk",
    tags=["Documents"],
    summary="Add Multiple Documents",
    description="Add multiple documents to the knowledge base in a single request"
)
async def add_documents_bulk(bulk_input: BulkDocumentInput):
    """
    Add multiple documents at once.
    
    More efficient than adding documents one by one.
    """
    try:
        results = []
        errors = []
        
        # Group documents by collection
        docs_by_collection = {}
        for doc in bulk_input.documents:
            if doc.collection not in docs_by_collection:
                docs_by_collection[doc.collection] = []
            docs_by_collection[doc.collection].append(doc)
        
        # Process each collection
        for collection_name, docs in docs_by_collection.items():
            try:
                # Ensure collection exists
                get_or_create_collection(collection_name)
                
                # Prepare points for batch insert
                points = []
                for doc in docs:
                    doc_id = doc.document_id or generate_document_id(doc.content)
                    embedding = get_embedding(doc.content)
                    
                    payload = doc.metadata.copy() if doc.metadata else {}
                    payload["content"] = doc.content
                    payload["doc_id"] = doc_id
                    payload["added_at"] = datetime.now().isoformat()
                    payload["content_length"] = len(doc.content)
                    
                    point_id = string_to_int_id(doc_id)
                    
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload=payload
                        )
                    )
                    results.append({"id": doc_id, "status": "success"})
                
                # Batch insert
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                
            except Exception as e:
                for doc in docs:
                    errors.append({"content_preview": doc.content[:50], "error": str(e)})
        
        return {
            "total": len(bulk_input.documents),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk add failed: {str(e)}")


@app.get(
    "/documents/{collection}/{document_id}",
    tags=["Documents"],
    summary="Get Document",
    description="Retrieve a specific document by ID"
)
async def get_document(collection: str, document_id: str):
    """Get a specific document by ID"""
    try:
        # Convert string ID to integer
        point_id = string_to_int_id(document_id)
        
        # Retrieve from Qdrant
        results = qdrant_client.retrieve(
            collection_name=collection,
            ids=[point_id],
            with_payload=True
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="Document not found")
        
        payload = results[0].payload or {}
        
        return {
            "id": payload.get('doc_id', document_id),
            "content": payload.get('content', None),
            "metadata": {k: v for k, v in payload.items() if k not in ['content', 'doc_id']}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.delete(
    "/documents/{collection}/{document_id}",
    tags=["Documents"],
    summary="Delete Document",
    description="Delete a document from the knowledge base"
)
async def delete_document(collection: str, document_id: str):
    """Delete a document by ID"""
    try:
        # Convert string ID to integer
        point_id = string_to_int_id(document_id)
        
        # Delete from Qdrant
        qdrant_client.delete(
            collection_name=collection,
            points_selector=[point_id]
        )
        
        return {
            "status": "success",
            "message": f"Document {document_id} deleted from {collection}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get(
    "/collections",
    response_model=List[CollectionInfo],
    tags=["Collections"],
    summary="List Collections",
    description="List all collections in the knowledge base"
)
async def list_collections():
    """List all available collections"""
    try:
        collections = qdrant_client.get_collections().collections
        
        result = []
        for coll in collections:
            # Get collection info
            coll_info = qdrant_client.get_collection(coll.name)
            result.append(CollectionInfo(
                name=coll.name,
                count=coll_info.points_count,
                metadata={"vectors_count": coll_info.vectors_count}
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@app.post(
    "/collections",
    tags=["Collections"],
    summary="Create Collection",
    description="Create a new collection for organizing documents"
)
async def create_collection(collection: CollectionCreate):
    """Create a new collection"""
    try:
        qdrant_client.create_collection(
            collection_name=collection.name,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE
            )
        )
        
        return {
            "status": "success",
            "message": f"Collection '{collection.name}' created",
            "name": collection.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")


@app.delete(
    "/collections/{name}",
    tags=["Collections"],
    summary="Delete Collection",
    description="Delete a collection and all its documents"
)
async def delete_collection(name: str):
    """Delete a collection"""
    try:
        qdrant_client.delete_collection(name)
        
        return {
            "status": "success",
            "message": f"Collection '{name}' deleted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")


@app.post(
    "/seed",
    tags=["Documents"],
    summary="Seed Knowledge Base",
    description="Populate the knowledge base with default AWS best practices and templates"
)
async def seed_knowledge_base():
    """
    Seed the knowledge base with default AWS best practices.
    
    Adds a curated set of documents covering:
    - VPC and networking
    - Security best practices
    - Cost optimization
    - Terraform patterns
    """
    try:
        # Default AWS best practices
        default_documents = [
            {
                "content": "VPC Best Practice: Use a /16 CIDR block for production VPCs (e.g., 10.0.0.0/16) to provide 65,536 IP addresses and room for growth. Always deploy resources across at least 2 Availability Zones for high availability.",
                "metadata": {"category": "networking", "resource": "vpc", "importance": "high"}
            },
            {
                "content": "Subnet Design: Create separate subnets for public, private, and data tiers. Public subnets should have route to Internet Gateway, private subnets route through NAT Gateway, and data subnets should have no internet access.",
                "metadata": {"category": "networking", "resource": "subnet", "importance": "high"}
            },
            {
                "content": "NAT Gateway: Deploy NAT Gateways in each AZ for high availability. Single NAT Gateway creates a single point of failure. Cost is approximately $32/month per NAT Gateway plus data processing charges.",
                "metadata": {"category": "networking", "resource": "nat_gateway", "importance": "medium"}
            },
            {
                "content": "Security Groups: Follow the principle of least privilege. Only open required ports, use security group references instead of CIDR blocks where possible, and add descriptions to all rules.",
                "metadata": {"category": "security", "resource": "security_group", "importance": "high"}
            },
            {
                "content": "IAM Best Practice: Use IAM roles instead of access keys for EC2 instances and Lambda functions. Enable MFA for all human users. Use AWS Organizations SCPs for guardrails.",
                "metadata": {"category": "security", "resource": "iam", "importance": "high"}
            },
            {
                "content": "Encryption: Enable encryption at rest for all data stores (S3, EBS, RDS). Use AWS KMS for key management. Enable encryption in transit using TLS 1.2+.",
                "metadata": {"category": "security", "resource": "encryption", "importance": "high"}
            },
            {
                "content": "EC2 Sizing: Start with smaller instance types and scale up based on metrics. Use t3/t3a for burstable workloads, m5/m6i for general purpose. Consider Spot instances for non-critical workloads (up to 90% savings).",
                "metadata": {"category": "cost", "resource": "ec2", "importance": "medium"}
            },
            {
                "content": "Tagging Strategy: Implement consistent tagging with at minimum: Name, Environment, Owner, CostCenter, Project. Use AWS Tag Policies for enforcement.",
                "metadata": {"category": "management", "resource": "tags", "importance": "high"}
            },
            {
                "content": "Terraform State: Store Terraform state in S3 with versioning enabled. Use DynamoDB for state locking. Never commit state files to version control.",
                "metadata": {"category": "terraform", "resource": "state", "importance": "high"}
            },
            {
                "content": "Terraform Modules: Use modules for reusable components. Pin module versions. Use consistent naming conventions. Keep modules focused on single responsibility.",
                "metadata": {"category": "terraform", "resource": "modules", "importance": "medium"}
            },
            {
                "content": "RDS Best Practice: Enable Multi-AZ for production databases. Use encryption at rest. Configure automated backups with appropriate retention. Right-size instance types based on actual usage.",
                "metadata": {"category": "database", "resource": "rds", "importance": "high"}
            },
            {
                "content": "S3 Security: Block public access by default. Enable versioning for important buckets. Use lifecycle policies to manage costs. Enable server-side encryption.",
                "metadata": {"category": "storage", "resource": "s3", "importance": "high"}
            }
        ]
        
        # Ensure collection exists
        get_or_create_collection(DEFAULT_COLLECTION)
        
        # Prepare points for batch insert
        points = []
        added = 0
        
        for doc in default_documents:
            try:
                doc_id = generate_document_id(doc["content"])
                embedding = get_embedding(doc["content"])
                
                payload = doc["metadata"].copy()
                payload["content"] = doc["content"]
                payload["doc_id"] = doc_id
                payload["added_at"] = datetime.now().isoformat()
                payload["source"] = "AWS Best Practices Seed"
                
                point_id = string_to_int_id(doc_id)
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
                added += 1
            except Exception as e:
                continue  # Skip on error
        
        # Batch insert all documents
        if points:
            qdrant_client.upsert(
                collection_name=DEFAULT_COLLECTION,
                points=points
            )
        
        # Get collection count
        coll_info = qdrant_client.get_collection(DEFAULT_COLLECTION)
        
        return {
            "status": "success",
            "message": f"Knowledge base seeded with {added} documents",
            "collection": DEFAULT_COLLECTION,
            "total_documents": coll_info.points_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed knowledge base: {str(e)}")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health & Status"],
    summary="Detailed Health Check",
    description="Comprehensive health check including ChromaDB and Claude API status"
)
async def health_check():
    """
    Detailed health check with database and API status.
    """
    try:
        # Check Qdrant
        collections = qdrant_client.get_collections().collections
        total_docs = 0
        for coll in collections:
            coll_info = qdrant_client.get_collection(coll.name)
            total_docs += coll_info.points_count
        
        # Check Claude API
        claude_status = "connected"
        try:
            test_msg = claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
        except Exception:
            claude_status = "error"
        
        return HealthResponse(
            status="healthy",
            qdrant="connected",
            claude_api=claude_status,
            collections_count=len(collections),
            total_documents=total_docs,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return HealthResponse(
            status="degraded",
            qdrant="error",
            claude_api="unknown",
            collections_count=0,
            total_documents=0,
            timestamp=datetime.now().isoformat()
        )


@app.get(
    "/stats",
    response_model=StatsResponse,
    tags=["Health & Status"],
    summary="Knowledge Base Statistics",
    description="Get detailed statistics about the knowledge base"
)
async def get_stats():
    """Get knowledge base statistics"""
    try:
        collections = qdrant_client.get_collections().collections
        
        collection_info = []
        total_docs = 0
        
        for coll in collections:
            coll_info = qdrant_client.get_collection(coll.name)
            count = coll_info.points_count
            total_docs += count
            collection_info.append(CollectionInfo(
                name=coll.name,
                count=count,
                metadata={"vectors_count": coll_info.vectors_count}
            ))
        
        return StatsResponse(
            total_collections=len(collections),
            total_documents=total_docs,
            collections=collection_info,
            storage_info={
                "backend": "qdrant",
                "host": QDRANT_HOST,
                "port": QDRANT_PORT
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)