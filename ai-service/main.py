"""
AI Service - Gemini Integration
Natural Language to Infrastructure Code Generation using Google Gemini
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import google.generativeai as genai
import httpx
import os
import json
import re
import logging
from datetime import datetime
from plan_validator import create_plan_validator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Service - Gemini",
    version="2.0.0",
    description="Natural Language to Infrastructure Code using Google Gemini"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set! Service will fail on API calls.")
else:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured successfully")

# Initialize Gemini model
# Using gemini-2.5-flash-lite for text generation (working, free tier)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Initialize Plan Validator
plan_validator = create_plan_validator(model)
logger.info("Terraform Plan Validator initialized")

# RAG Service URL
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8002")


# ============== Pydantic Models ==============

class ParseIntentRequest(BaseModel):
    message: str = Field(..., description="Natural language infrastructure request")
    user_id: Optional[str] = Field(default="default", description="User identifier")

class ParseIntentResponse(BaseModel):
    intent: Dict[str, Any]
    message: str
    cached: bool = False

class GenerateCodeRequest(BaseModel):
    intent: Dict[str, Any]
    best_practices: Optional[list] = None

class GenerateCodeResponse(BaseModel):
    terraform_code: str
    explanation: str
    resources: list
    estimated_cost: str

class ValidatePlanRequest(BaseModel):
    plan_output: str = Field(..., description="Terraform plan output")
    terraform_code: str = Field(..., description="Original Terraform code")
    deployment_id: Optional[str] = Field(default=None, description="Deployment identifier")

class ValidatePlanResponse(BaseModel):
    has_errors: bool
    errors: List[Dict[str, Any]]
    fixes_applied: List[str]
    fixed_code: str
    analysis: str
    suggestions: Optional[List[str]] = []
    needs_human_review: bool
    auto_fix_successful: bool


# ============== Helper Functions ==============

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from Gemini response that might contain markdown"""
    try:
        # Try direct JSON parse first
        return json.loads(text)
    except json.JSONDecodeError:
        # Look for JSON in markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without code blocks
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        raise ValueError("No valid JSON found in response")


async def check_intent_cache(user_request: str) -> Optional[Dict]:
    """Check if intent is cached in RAG service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/intent/check-cache",
                json={"user_request": user_request}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("cached"):
                    logger.info(f"Cache HIT for request: {user_request[:50]}...")
                    return result.get("intent")
                else:
                    logger.info(f"Cache MISS for request: {user_request[:50]}...")
            return None
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
        return None


async def store_intent_cache(user_request: str, intent: Dict):
    """Store parsed intent in cache"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{RAG_SERVICE_URL}/intent/store",
                json={
                    "user_request": user_request,
                    "intent": intent
                }
            )
            logger.info("Intent cached successfully")
    except Exception as e:
        logger.warning(f"Failed to cache intent: {e}")


def remove_provider_blocks(terraform_code: str) -> str:
    """
    Remove provider and terraform blocks from generated code
    These blocks cause duplicate provider errors
    """
    import re
    
    # Remove provider "aws" blocks
    terraform_code = re.sub(
        r'provider\s+"aws"\s*{[^}]*}',
        '',
        terraform_code,
        flags=re.DOTALL
    )
    
    # Remove terraform blocks
    terraform_code = re.sub(
        r'terraform\s*{[^}]*}',
        '',
        terraform_code,
        flags=re.DOTALL
    )
    
    # Remove required_providers blocks
    terraform_code = re.sub(
        r'required_providers\s*{[^}]*}',
        '',
        terraform_code,
        flags=re.DOTALL
    )
    
    # Clean up extra newlines
    terraform_code = re.sub(r'\n{3,}', '\n\n', terraform_code)
    
    logger.info("Stripped provider/terraform blocks from generated code")
    
    return terraform_code.strip()


def validate_terraform_syntax(terraform_code: str) -> dict:
    """Validate Terraform code for common syntax errors"""
    errors = []
    warnings = []
    
    # Check for invalid attributes
    invalid_patterns = [
        (r'name_description\s*=', 'name_description', 'Use "description" instead'),
        (r'subnet_type\s*=', 'subnet_type', 'Use tags = { Type = "..." } instead'),
        (r'instance_name\s*=', 'instance_name', 'Use tags = { Name = "..." } instead'),
        (r'vpc_name\s*=', 'vpc_name', 'Use tags = { Name = "..." } instead'),
    ]
    
    for pattern, attribute, suggestion in invalid_patterns:
        if re.search(pattern, terraform_code):
            errors.append({
                'severity': 'error',
                'message': f'Invalid attribute: {attribute}',
                'suggestion': suggestion,
                'attribute': attribute
            })
    
    # Check for security group description
    if 'aws_security_group' in terraform_code:
        sg_blocks = re.findall(
            r'resource\s+"aws_security_group"\s+"[^"]+"\s+\{[^}]+\}',
            terraform_code,
            re.DOTALL
        )
        for sg_block in sg_blocks:
            if 'description' not in sg_block:
                errors.append({
                    'severity': 'error',
                    'message': 'Security group missing required "description" attribute',
                    'suggestion': 'Add: description = "Security group for ..."'
                })
    
    return {
        'valid': len([e for e in errors if e['severity'] == 'error']) == 0,
        'errors': errors,
        'warnings': warnings,
        'critical_errors': [e for e in errors if e['severity'] == 'error']
    }


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AI Service - Gemini",
        "status": "healthy",
        "model": "gemini-pro",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.post("/parse-intent", response_model=ParseIntentResponse)
async def parse_intent(request: ParseIntentRequest):
    """
    Parse natural language request into structured intent using Gemini
    """
    try:
        # Check cache first
        cached_intent = await check_intent_cache(request.message)
        if cached_intent:
            return ParseIntentResponse(
                intent=cached_intent,
                message="Intent retrieved from cache",
                cached=True
            )
        
        # Create prompt for Gemini
        prompt = f"""You are an AWS infrastructure expert. Parse this natural language request into a structured JSON intent.

User Request: {request.message}

Extract the following information:
1. resources: List of AWS resources needed (e.g., vpc, subnet, ec2, rds, s3)
2. region: AWS region (default: us-east-1)
3. environment: Environment type (dev, staging, production)
4. requirements: Specific requirements mentioned
5. constraints: Any limitations or constraints

Respond with ONLY valid JSON in this exact format:
{{
  "resources": ["list", "of", "resources"],
  "region": "us-east-1",
  "environment": "production",
  "requirements": ["requirement1", "requirement2"],
  "constraints": ["constraint1"],
  "summary": "Brief summary of what to create"
}}"""

        # Call Gemini
        logger.info("Calling Gemini API for intent parsing...")
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        intent_data = extract_json_from_text(response.text)
        
        logger.info(f"Intent parsed successfully: {intent_data.get('summary', 'N/A')}")
        
        # Cache the result (non-blocking)
        await store_intent_cache(request.message, intent_data)
        
        return ParseIntentResponse(
            intent=intent_data,
            message="Intent parsed successfully using Gemini",
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Intent parsing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse intent: {str(e)}"
        )


@app.post("/generate-code", response_model=GenerateCodeResponse)
async def generate_code(request: GenerateCodeRequest):
    """
    Generate Terraform code from structured intent using Gemini
    """
    try:
        intent = request.intent
        best_practices = request.best_practices or []
        
        # Build context from best practices
        context = ""
        if best_practices:
            context = "\n\nAWS Best Practices:\n"
            for practice in best_practices[:3]:  # Use top 3
                context += f"- {practice.get('content', '')}\n"
        
        # Create comprehensive prompt
        prompt = f"""You are a Terraform expert. Generate production-ready Terraform code based on this intent.

Intent:
{json.dumps(intent, indent=2)}
{context}

=== TERRAFORM SYNTAX RULES (CRITICAL) ===

Common AWS Resource Attributes:

aws_vpc:
  - cidr_block (REQUIRED)
  - enable_dns_hostnames
  - enable_dns_support
  - tags

aws_subnet:
  - vpc_id (REQUIRED)
  - cidr_block (REQUIRED)
  - availability_zone
  - map_public_ip_on_launch
  - tags

aws_security_group:
  - name (REQUIRED)
  - description (REQUIRED) ← NEVER use "name_description"
  - vpc_id
  - ingress
  - egress
  - tags

aws_instance:
  - ami (REQUIRED)
  - instance_type (REQUIRED)
  - subnet_id
  - vpc_security_group_ids
  - tags

NEVER use these invalid attributes:
  ✗ name_description (use "description")
  ✗ subnet_type (use tags)
  ✗ instance_name (use tags.Name)
  ✗ vpc_name (use tags.Name)

ALWAYS use tags for naming:
  tags = {{
    Name = "my-resource-name"
    Environment = "production"
  }}

Generate:
1. Complete, valid Terraform code
2. Brief explanation
3. List of resources created
4. Estimated monthly cost

Respond with ONLY valid JSON:
{{
  "terraform_code": "complete terraform code here",
  "explanation": "what this infrastructure does",
  "resources": ["aws_vpc.main", "aws_subnet.public"],
  "estimated_cost": "$50/month"
}}"""

        # Call Gemini
        logger.info("Calling Gemini API for code generation...")
        response = model.generate_content(prompt)
        
        # Extract JSON
        code_data = extract_json_from_text(response.text)
        
        # Strip provider blocks if Gemini included them anyway
        terraform_code = code_data.get('terraform_code', '')
        terraform_code = remove_provider_blocks(terraform_code)
        code_data['terraform_code'] = terraform_code
        
        # Validate syntax
        validation_result = validate_terraform_syntax(terraform_code)
        
        if not validation_result['valid']:
            logger.warning(f"Syntax errors found: {validation_result['critical_errors']}")
            
            # Auto-fix common issues
            fixed_code = terraform_code
            for error in validation_result['critical_errors']:
                if error.get('attribute') == 'name_description':
                    fixed_code = re.sub(
                        r'name_description\s*=',
                        'description =',
                        fixed_code
                    )
                    logger.info("Auto-fixed: name_description → description")
            
            # Re-validate
            code_data['terraform_code'] = fixed_code
            revalidation = validate_terraform_syntax(fixed_code)
            if revalidation['valid']:
                logger.info("Auto-fix successful!")
        
        logger.info("Code generated successfully")
        
        return GenerateCodeResponse(
            terraform_code=code_data.get('terraform_code', ''),
            explanation=code_data.get('explanation', ''),
            resources=code_data.get('resources', []),
            estimated_cost=code_data.get('estimated_cost', 'Unknown')
        )
        
    except Exception as e:
        logger.error(f"Code generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate code: {str(e)}"
        )


@app.post("/validate-plan", response_model=ValidatePlanResponse)
async def validate_terraform_plan(request: ValidatePlanRequest):
    """
    Validate Terraform plan output and automatically fix issues
    
    This endpoint:
    1. Analyzes terraform plan output for errors
    2. Uses AI to understand root causes
    3. Automatically applies fixes where possible
    4. Returns fixed code or suggests manual fixes
    """
    try:
        logger.info(f"Validating Terraform plan for deployment: {request.deployment_id}")
        
        # Run validation
        result = plan_validator.validate_and_fix(
            plan_output=request.plan_output,
            terraform_code=request.terraform_code
        )
        
        # Determine if auto-fix was successful
        auto_fix_successful = (
            result['has_errors'] and 
            len(result['fixes_applied']) > 0 and
            not result['needs_human_review']
        )
        
        logger.info(f"Validation complete. Errors: {result['has_errors']}, " +
                   f"Fixes applied: {len(result['fixes_applied'])}, " +
                   f"Needs review: {result['needs_human_review']}")
        
        return ValidatePlanResponse(
            has_errors=result['has_errors'],
            errors=result['errors'],
            fixes_applied=result['fixes_applied'],
            fixed_code=result['fixed_code'],
            analysis=result['analysis'],
            suggestions=result.get('suggestions', []),
            needs_human_review=result['needs_human_review'],
            auto_fix_successful=auto_fix_successful
        )
        
    except Exception as e:
        logger.error(f"Plan validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate plan: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model": "gemini-pro",
        "api_configured": bool(GEMINI_API_KEY),
        "rag_service": RAG_SERVICE_URL,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)