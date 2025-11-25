"""
Utility functions for AI Service
Handles Claude API interactions, JSON parsing, and helper functions
"""

import json
import re
from typing import Dict, Any, Optional
import anthropic
from config import settings
import logging

logger = logging.getLogger(__name__)


class ClaudeAPIHandler:
    """Handler for Claude AI API interactions"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.MAX_TOKENS
    
    async def send_message(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send a message to Claude and get response
        
        Args:
            prompt: The prompt to send
            max_tokens: Override default max tokens
            
        Returns:
            Response text from Claude
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            logger.info(f"Claude API response received, length: {len(response_text)}")
            
            return response_text
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {str(e)}")
            raise Exception(f"Claude API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {str(e)}")
            raise Exception(f"Failed to communicate with Claude: {str(e)}")
    
    async def send_message_json(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send message and expect JSON response
        
        Args:
            prompt: The prompt to send
            max_tokens: Override default max tokens
            
        Returns:
            Parsed JSON response
        """
        response_text = await self.send_message(prompt, max_tokens)
        return parse_json_response(response_text)


def parse_json_response(text: str) -> Dict[str, Any]:
    """
    Parse JSON from Claude's response, handling markdown code blocks
    
    Args:
        text: Raw response text from Claude
        
    Returns:
        Parsed JSON object
        
    Raises:
        ValueError: If JSON cannot be parsed
    """
    try:
        # Remove markdown code blocks
        text = text.strip()
        
        # Pattern 1: ```json ... ```
        if text.startswith("```"):
            # Split by ``` and get the content between first and second ```
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1]
                # Remove language identifier if present
                if text.startswith("json"):
                    text = text[4:]
                elif text.startswith("JSON"):
                    text = text[4:]
        
        text = text.strip()
        
        # Try to parse
        return json.loads(text)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}\nText: {text}")
        raise ValueError(f"Invalid JSON response from Claude: {str(e)}")


def extract_terraform_code(text: str) -> str:
    """
    Extract Terraform code from response, handling code blocks
    
    Args:
        text: Text containing Terraform code
        
    Returns:
        Clean Terraform code
    """
    # If it's wrapped in code blocks, extract it
    if "```" in text:
        # Find content between ```terraform or ```hcl or ``` and next ```
        pattern = r"```(?:terraform|hcl)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    return text.strip()


def estimate_complexity(resources: list, requirements: dict) -> str:
    """
    Estimate infrastructure complexity based on resources and requirements
    
    Args:
        resources: List of AWS resources
        requirements: Dictionary of requirements
        
    Returns:
        Complexity level: 'simple', 'moderate', or 'complex'
    """
    resource_count = len(resources)
    
    # Check for complexity keywords
    text = " ".join([str(v) for v in requirements.values()]).lower()
    
    if any(kw in text for kw in ["enterprise", "production", "high availability", "multi-region"]):
        return "complex"
    
    if resource_count <= 3:
        return "simple"
    elif resource_count <= 10:
        return "moderate"
    else:
        return "complex"


def identify_aws_resources(text: str) -> list:
    """
    Identify AWS resources mentioned in text
    
    Args:
        text: Natural language text
        
    Returns:
        List of identified AWS resource types
    """
    from config import AWS_RESOURCE_KEYWORDS
    
    text_lower = text.lower()
    resources = set()
    
    for resource, keywords in AWS_RESOURCE_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            resources.add(resource)
    
    return sorted(list(resources))


def build_rag_context(rag_results: list) -> str:
    """
    Build formatted context string from RAG search results
    
    Args:
        rag_results: List of documents from RAG service
        
    Returns:
        Formatted context string
    """
    if not rag_results:
        return ""
    
    context = "\n\n=== BEST PRACTICES FROM KNOWLEDGE BASE ===\n"
    
    for idx, doc in enumerate(rag_results, 1):
        title = doc.get("metadata", {}).get("title", "Document")
        content = doc.get("content", "")
        score = doc.get("score", 0)
        
        context += f"\n{idx}. {title} (Relevance: {score:.2f})\n"
        context += f"{content}\n"
        context += "-" * 50 + "\n"
    
    return context


def build_policy_context(policies: dict) -> str:
    """
    Build formatted policy context string
    
    Args:
        policies: Dictionary of organization policies
        
    Returns:
        Formatted policy string
    """
    if not policies:
        return ""
    
    context = "\n\n=== ORGANIZATION POLICIES ===\n"
    
    for policy_name, policy_rules in policies.items():
        context += f"\n{policy_name}:\n"
        if isinstance(policy_rules, dict):
            for key, value in policy_rules.items():
                context += f"  - {key}: {value}\n"
        else:
            context += f"  {policy_rules}\n"
    
    return context


def validate_terraform_syntax(code: str) -> tuple[bool, Optional[str]]:
    """
    Basic Terraform syntax validation
    
    Args:
        code: Terraform code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic checks
    if not code.strip():
        return False, "Empty Terraform code"
    
    # Check for required blocks
    if "resource" not in code and "module" not in code:
        return False, "No resource or module blocks found"
    
    # Check for balanced braces
    if code.count("{") != code.count("}"):
        return False, "Unbalanced braces in Terraform code"
    
    # Check for provider block (recommended)
    if "provider" not in code:
        logger.warning("No provider block found in Terraform code")
    
    return True, None


async def retry_with_backoff(func, max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Retry a function with exponential backoff
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        backoff_factor: Multiplier for backoff delay
        
    Returns:
        Result from function
    """
    import asyncio
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = backoff_factor ** attempt
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
            await asyncio.sleep(delay)