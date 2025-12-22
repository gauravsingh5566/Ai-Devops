"""
Utility functions for RAG Service
Handles document chunking, embedding generation, and helper functions
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def chunk_document(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Split a document into overlapping chunks for better retrieval.
    
    Args:
        text: Document text to chunk
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between consecutive chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find end of chunk
        end = start + chunk_size
        
        # If not at the end, try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            
            # Use the latest sentence boundary
            break_point = max(last_period, last_newline)
            
            if break_point > start:
                end = break_point + 1
        
        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start with overlap
        start = end - chunk_overlap
        
        # Avoid infinite loop
        if start <= 0 or (len(chunks) > 0 and start >= len(text)):
            break
    
    return chunks


def generate_document_id(content: str, prefix: str = "doc") -> str:
    """
    Generate unique document ID based on content hash.
    
    Args:
        content: Document content
        prefix: ID prefix
        
    Returns:
        Unique document ID
    """
    content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
    return f"{prefix}_{content_hash}"


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_keywords(text: str) -> List[str]:
    """
    Extract important keywords from text.
    
    Args:
        text: Document text
        
    Returns:
        List of keywords
    """
    # Common AWS/infrastructure terms to look for
    aws_terms = [
        'vpc', 'subnet', 'ec2', 'rds', 's3', 'lambda', 'ecs', 'eks',
        'iam', 'security group', 'nat gateway', 'internet gateway',
        'route table', 'alb', 'nlb', 'cloudfront', 'route53',
        'terraform', 'cloudformation', 'encryption', 'kms',
        'multi-az', 'high availability', 'auto scaling', 'load balancer'
    ]
    
    text_lower = text.lower()
    found_terms = []
    
    for term in aws_terms:
        if term in text_lower:
            found_terms.append(term)
    
    return found_terms


def calculate_similarity(score: float) -> str:
    """
    Convert similarity score to human-readable label.
    
    Args:
        score: Similarity score (0-1)
        
    Returns:
        Label: 'high', 'medium', 'low'
    """
    if score >= 0.8:
        return "high"
    elif score >= 0.5:
        return "medium"
    else:
        return "low"


def format_search_results(
    results: Dict[str, Any],
    include_metadata: bool = True
) -> List[Dict]:
    """
    Format ChromaDB search results into clean structure.
    
    Args:
        results: Raw ChromaDB results
        include_metadata: Whether to include metadata
        
    Returns:
        Formatted results list
    """
    formatted = []
    
    if not results or not results.get('ids'):
        return formatted
    
    for i, doc_id in enumerate(results['ids'][0]):
        result = {
            'id': doc_id,
            'content': results['documents'][0][i] if results.get('documents') else None,
            'score': 1 - results['distances'][0][i] if results.get('distances') else 0
        }
        
        if include_metadata and results.get('metadatas'):
            result['metadata'] = results['metadatas'][0][i]
        
        formatted.append(result)
    
    return formatted


def validate_metadata(metadata: Dict) -> Dict:
    """
    Validate and clean metadata.
    
    Args:
        metadata: Raw metadata
        
    Returns:
        Validated metadata
    """
    from config import DOCUMENT_CATEGORIES, IMPORTANCE_LEVELS
    
    validated = {}
    
    for key, value in metadata.items():
        # Ensure values are strings (ChromaDB requirement)
        if isinstance(value, (list, dict)):
            validated[key] = str(value)
        elif isinstance(value, bool):
            validated[key] = str(value).lower()
        else:
            validated[key] = str(value) if value is not None else ""
    
    # Validate category
    if 'category' in validated:
        if validated['category'] not in DOCUMENT_CATEGORIES:
            logger.warning(f"Unknown category: {validated['category']}")
    
    # Validate importance
    if 'importance' in validated:
        if validated['importance'] not in IMPORTANCE_LEVELS:
            validated['importance'] = 'medium'
    
    return validated


def merge_documents(docs: List[str], separator: str = "\n\n") -> str:
    """
    Merge multiple documents into one.
    
    Args:
        docs: List of document contents
        separator: Separator between documents
        
    Returns:
        Merged document
    """
    return separator.join(doc.strip() for doc in docs if doc.strip())


def create_context_string(search_results: List[Dict]) -> str:
    """
    Create a context string from search results for AI Service.
    
    Args:
        search_results: List of search results
        
    Returns:
        Formatted context string
    """
    if not search_results:
        return ""
    
    context_parts = []
    
    for i, result in enumerate(search_results, 1):
        content = result.get('content', '')
        metadata = result.get('metadata', {})
        score = result.get('score', 0)
        
        source = metadata.get('source', 'Unknown')
        category = metadata.get('category', 'general')
        
        context_parts.append(
            f"[{i}] ({category.upper()}, Relevance: {score:.2f})\n"
            f"Source: {source}\n"
            f"{content}"
        )
    
    return "\n\n---\n\n".join(context_parts)


def estimate_tokens(text: str) -> int:
    """
    Estimate number of tokens in text.
    
    Rough estimation: ~4 characters per token for English.
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximately max tokens.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum tokens
        
    Returns:
        Truncated text
    """
    max_chars = max_tokens * 4
    
    if len(text) <= max_chars:
        return text
    
    # Try to truncate at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    
    if last_period > max_chars * 0.8:
        return truncated[:last_period + 1]
    
    return truncated + "..."


class DocumentProcessor:
    """Process documents for storage in vector database"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_length: int = 10000
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_length = max_length
    
    def process(self, content: str, metadata: Dict = None) -> List[Dict]:
        """
        Process a document into chunks with metadata.
        
        Args:
            content: Document content
            metadata: Optional metadata
            
        Returns:
            List of processed chunks
        """
        # Clean text
        content = clean_text(content)
        
        # Truncate if too long
        if len(content) > self.max_length:
            content = content[:self.max_length]
            logger.warning(f"Document truncated to {self.max_length} characters")
        
        # Chunk document
        chunks = chunk_document(
            content,
            self.chunk_size,
            self.chunk_overlap
        )
        
        # Process each chunk
        processed = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = validate_metadata(metadata or {})
            chunk_metadata['chunk_index'] = str(i)
            chunk_metadata['total_chunks'] = str(len(chunks))
            
            # Extract keywords
            keywords = extract_keywords(chunk)
            if keywords:
                chunk_metadata['keywords'] = ','.join(keywords[:5])
            
            processed.append({
                'id': f"{generate_document_id(content)}_{i}",
                'content': chunk,
                'metadata': chunk_metadata
            })
        
        return processed


def get_embedding_simple(text: str, dimension: int = 384) -> List[float]:
    """
    Generate a simple deterministic embedding for text.
    
    Note: This is a placeholder. In production, use a proper
    embedding model like OpenAI embeddings or sentence-transformers.
    
    Args:
        text: Text to embed
        dimension: Embedding dimension
        
    Returns:
        Embedding vector
    """
    # Create deterministic hash-based embedding
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    
    embedding = []
    for i in range(0, min(len(text_hash), dimension * 2), 2):
        byte_val = int(text_hash[i:i+2], 16)
        embedding.append((byte_val - 128) / 128.0)
    
    # Pad if needed
    while len(embedding) < dimension:
        embedding.append(0.0)
    
    return embedding[:dimension]
