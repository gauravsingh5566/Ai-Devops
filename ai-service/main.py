"""
AI Service - Gemini Integration
Natural Language to Infrastructure Code Generation using Google Gemini
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import google.generativeai as genai
import httpx
import os
import json
import re
import hashlib
import logging
from datetime import datetime
from plan_validator import create_plan_validator
from rag_client import create_rag_client
from chat_manager import ChatManager
from conversation_ai import ConversationAI

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

# RAG Service URL
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8002")

# Create RAG client for Terraform examples
rag_client = create_rag_client(RAG_SERVICE_URL)

# Initialize Plan Validator with RAG connection
plan_validator = create_plan_validator(model, terraform_store=rag_client)
logger.info("Terraform Plan Validator initialized with RAG connection")

# Initialize Chat Manager and Conversation AI
chat_manager = ChatManager()
conversation_ai = ConversationAI(model)
logger.info("Chat system initialized")


# ============== Pydantic Models ==============

class ParseIntentRequest(BaseModel):
    message: str = Field(..., description="Natural language infrastructure request")
    user_id: Optional[str] = Field(default="default", description="User identifier")

class ParseIntentResponse(BaseModel):
    intent: Dict[str, Any]
    message: str
    cached: bool = False
    user_request: Optional[str] = None  # Original user message
    matching_templates: Optional[List[Dict]] = []  # Matching infrastructure templates

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

async def store_generated_terraform(
    terraform_code: str,
    intent: Dict[str, Any],
    resources: List[str],
    user_request: str
):
    """
    Store generated Terraform code in RAG service immediately after generation
    """
    try:
        # Extract resource types
        resource_pattern = r'resource\s+"(aws_\w+)"\s+"(\w+)"'
        resource_types = list(set([m[0] for m in re.findall(resource_pattern, terraform_code)]))
        
        if not resource_types:
            resource_types = [r.split('.')[0] for r in resources if '.' in r]
        
        # Generate unique ID
        code_hash = hashlib.sha256(terraform_code.encode()).hexdigest()[:16]
        deployment_id = f"gen_{code_hash}"
        
        # Create description from intent (handle missing keys)
        description = intent.get('summary', intent.get('description', user_request[:200]))
        if not description or description == user_request[:200]:
            # Fallback: create description from resources
            description = f"Infrastructure with {', '.join(resource_types[:3])}"
        
        logger.info(f"Storing generated Terraform: {deployment_id}")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/terraform/store",
                json={
                    "terraform_code": terraform_code,
                    "deployment_id": deployment_id,
                    "resource_types": resource_types,
                    "description": description,
                    "metadata": {
                        "source": "ai_generation",
                        "intent": intent,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Stored generated Terraform in Qdrant: {deployment_id}")
                return True
            else:
                logger.warning(f"Failed to store in RAG: {response.status_code}")
                return False
                
    except Exception as e:
        logger.warning(f"Could not store generated Terraform: {e}")
        return False


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
            cached_intent['user_request'] = request.message
            
            # Search templates even for cached intents
            matching_templates = []
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    template_response = await client.post(
                        f"{RAG_SERVICE_URL}/templates/search",
                        json={
                            "user_requirement": request.message,
                            "top_k": 3
                        }
                    )
                    if template_response.status_code == 200:
                        matching_templates = template_response.json()
            except Exception as e:
                logger.warning(f"Could not fetch templates: {e}")
            
            return ParseIntentResponse(
                intent=cached_intent,
                message="Intent retrieved from cache",
                cached=True,
                user_request=request.message,
                matching_templates=matching_templates
            )
        
        # Search for matching templates FIRST (before calling Gemini)
        matching_templates = []
        template_context = ""
        try:
            logger.info(f"Searching infrastructure templates for: {request.message[:100]}")
            async with httpx.AsyncClient(timeout=5.0) as client:
                template_response = await client.post(
                    f"{RAG_SERVICE_URL}/templates/search",
                    json={
                        "user_requirement": request.message,
                        "top_k": 2
                    }
                )
                
                if template_response.status_code == 200:
                    matching_templates = template_response.json()
                    if matching_templates:
                        logger.info(f"✅ Found {len(matching_templates)} matching templates")
                        
                        # Build template context for AI prompt
                        template_context = "\n\nMATCHING INFRASTRUCTURE TEMPLATES:\n"
                        for idx, template in enumerate(matching_templates, 1):
                            logger.info(f"  • {template['name']} (Match: {template.get('similarity_score', 0):.0%})")
                            template_context += f"\nTemplate {idx}: {template['name']} (Match: {template.get('similarity_score', 0):.0%})\n"
                            template_context += f"Recommended AWS Resources:\n"
                            
                            # Add services from template
                            services = template.get('services', {})
                            for category, service_list in services.items():
                                template_context += f"  {category}: {', '.join(service_list)}\n"
                            
                            template_context += f"Components: {', '.join(template.get('components', [])[:5])}\n"
                    else:
                        logger.info("No matching templates found")
        except Exception as e:
            logger.warning(f"Could not fetch templates: {e}")
        
        # Create prompt for Gemini with template recommendations
        prompt = f"""You are an AWS infrastructure expert. Parse this natural language request into a structured JSON intent.

User Request: {request.message}
{template_context}

IMPORTANT: If matching templates are provided above, use their recommended services and resources in your response.

Extract the following information:
1. resources: List of AWS resources needed based on templates (e.g., vpc, subnet, ecs, rds, elasticache, alb)
   - If templates suggest ECS Fargate, include: ecs, ecs_service, ecs_task_definition
   - If templates suggest RDS, include: rds
   - If templates suggest Load Balancer, include: alb, target_group
   - If templates suggest ElastiCache, include: elasticache
   - Include ALL resources mentioned in the matching template services
2. region: AWS region (default: us-east-1)
3. environment: Environment type (dev, staging, production)
4. requirements: Specific requirements mentioned by user
5. constraints: Any limitations or constraints
6. recommended_template: If templates match well (>50%), include the template_id of best match

Respond with ONLY valid JSON in this exact format:
{{
  "resources": ["vpc", "subnet", "ecs", "ecs_service", "alb", "target_group", "rds", "elasticache", "security_group"],
  "region": "us-east-1",
  "environment": "production",
  "requirements": ["requirement1", "requirement2"],
  "constraints": ["constraint1"],
  "summary": "Brief summary of what to create",
  "recommended_template": "microservices-arch"
}}"""

        # Call Gemini
        logger.info("Calling Gemini API for intent parsing...")
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        intent_data = extract_json_from_text(response.text)
        
        logger.info(f"Intent parsed successfully: {intent_data.get('summary', 'N/A')}")
        
        # Templates already fetched above, just log count
        if matching_templates:
            logger.info(f"Returning {len(matching_templates)} matching templates with intent")
        
        # Cache the result (non-blocking)
        await store_intent_cache(request.message, intent_data)
        
        # Add original user request to intent
        intent_data['user_request'] = request.message
        
        return ParseIntentResponse(
            intent=intent_data,
            message="Intent parsed successfully using Gemini",
            cached=False,
            user_request=request.message,
            matching_templates=matching_templates
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
        
        # NEW: Search for matching infrastructure templates
        template_context = ""
        try:
            # Get user request from intent
            user_req = intent.get('user_request', '') or intent.get('summary', '')
            
            if user_req:
                logger.info(f"Searching templates for: {user_req[:100]}")
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{RAG_SERVICE_URL}/templates/search",
                        json={
                            "user_requirement": user_req,
                            "top_k": 2
                        }
                    )
                    
                    if response.status_code == 200:
                        templates = response.json()
                        if templates:
                            template_context = "\n\n🎯 MATCHING INFRASTRUCTURE TEMPLATES FROM DATABASE:\n"
                            for idx, template in enumerate(templates, 1):
                                template_context += f"\n--- Template {idx}: {template['name']} (Match: {template.get('similarity_score', 0):.0%}) ---\n"
                                template_context += f"Use Case: {template['use_case']}\n"
                                template_context += f"Recommended Components:\n"
                                for comp in template['components'][:8]:  # Top 8 components
                                    template_context += f"  • {comp}\n"
                                
                                # Show services by category
                                services = template.get('services', {})
                                if services:
                                    template_context += f"Services to Use:\n"
                                    for category, service_list in list(services.items())[:3]:
                                        template_context += f"  {category}: {', '.join(service_list[:3])}\n"
                                
                                template_context += f"Estimated Cost: {template['estimated_cost']}\n"
                            
                            logger.info(f"✅ Found {len(templates)} matching templates for code generation")
                        else:
                            logger.info("No matching templates found")
            else:
                logger.warning("No user_request found in intent for template search")
                
        except Exception as e:
            logger.warning(f"Could not fetch templates: {e}")
        
        # Build context from best practices
        context = ""
        if best_practices:
            context = "\n\nAWS Best Practices:\n"
            for practice in best_practices[:3]:  # Use top 3
                context += f"- {practice.get('content', '')}\n"
        
        # Add template context to prompt
        context += template_context
        
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
        
        # Store generated Terraform in RAG (don't wait for deployment)
        try:
            # Get user request from intent or use summary
            user_req = intent.get('summary', 'Generated Infrastructure')
            
            await store_generated_terraform(
                terraform_code=code_data.get('terraform_code', ''),
                intent=intent,
                resources=code_data.get('resources', []),
                user_request=user_req
            )
        except Exception as e:
            logger.warning(f"Failed to store generated code: {e}")
        
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


# ============== CHAT ENDPOINTS ==============

@app.websocket("/ws/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat with AI
    
    Usage:
    - Connect: ws://localhost:8001/ws/chat/user123
    - Send: {"message": "Deploy microservices"}
    - Receive: {"type": "message", "role": "assistant", "content": "...", "options": [...]}
    """
    await websocket.accept()
    logger.info(f"Chat WebSocket connected: {user_id}")
    
    # Create new chat session
    session = chat_manager.create_session(user_id)
    
    try:
        # Send greeting
        greeting = chat_manager.generate_greeting()
        session.add_message('assistant', greeting)
        
        await websocket.send_json({
            'type': 'message',
            'role': 'assistant',
            'content': greeting,
            'session_id': session.session_id,
            'progress': {
                'current': 0,
                'total': session.total_questions
            }
        })
        
        # Message loop
        while True:
            # Receive user message
            data = await websocket.receive_json()
            user_message = data.get('message', '')
            
            if not user_message:
                continue
            
            logger.info(f"User message: {user_message[:100]}")
            
            # Add user message to session
            session.add_message('user', user_message)
            
            # Determine conversation type from first message
            if session.current_question == 1:
                session.conversation_type = chat_manager.determine_conversation_type(user_message)
                logger.info(f"Conversation type: {session.conversation_type}")
            
            # Generate AI response
            ai_response = await conversation_ai.generate_response(session, user_message)
            
            # Add AI message to session
            session.add_message('assistant', ai_response['message'], ai_response.get('options'))
            
            # Update progress
            session.current_question += 1
            
            # Send response to client
            response_data = {
                'type': 'message',
                'role': 'assistant',
                'content': ai_response['message'],
                'options': ai_response.get('options'),
                'progress': {
                    'current': session.current_question,
                    'total': session.total_questions
                }
            }
            
            await websocket.send_json(response_data)
            
            # Check if conversation complete
            if ai_response.get('complete'):
                # Wait for user confirmation
                confirm_data = await websocket.receive_json()
                confirm_message = confirm_data.get('message', '').lower()
                
                if 'yes' in confirm_message or 'generate' in confirm_message:
                    # Send completion with intent
                    await websocket.send_json({
                        'type': 'complete',
                        'intent': ai_response['summary']['intent'],
                        'context': ai_response['summary']['context'],
                        'conversation_type': ai_response['summary']['conversation_type']
                    })
                    
                    # Mark session as completed
                    session.completed = True
                    logger.info(f"Chat session completed: {session.session_id}")
                    break
                else:
                    # User wants to change something
                    await websocket.send_json({
                        'type': 'message',
                        'role': 'assistant',
                        'content': "Sure! What would you like to change?",
                        'options': None
                    })
                    session.current_question -= 1  # Go back
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            'type': 'error',
            'message': f"An error occurred: {str(e)}"
        })
    finally:
        # Clean up session after 1 hour
        # (In production, you'd want to persist this to database)
        pass


@app.post("/chat/start")
async def start_chat_session(user_id: str = "default"):
    """
    Start a new chat session (HTTP alternative to WebSocket)
    
    Returns session_id and greeting message
    """
    session = chat_manager.create_session(user_id)
    greeting = chat_manager.generate_greeting()
    session.add_message('assistant', greeting)
    
    return {
        "session_id": session.session_id,
        "message": greeting,
        "progress": {
            "current": 0,
            "total": session.total_questions
        }
    }


@app.post("/chat/message")
async def send_chat_message(
    session_id: str,
    message: str
):
    """
    Send message in existing chat session (HTTP alternative)
    """
    session = chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message
    session.add_message('user', message)
    
    # Determine conversation type from first message
    if session.current_question == 1:
        session.conversation_type = chat_manager.determine_conversation_type(message)
    
    # Generate AI response
    ai_response = await conversation_ai.generate_response(session, message)
    
    # Add AI message
    session.add_message('assistant', ai_response['message'], ai_response.get('options'))
    
    # Update progress
    session.current_question += 1
    
    return {
        "message": ai_response['message'],
        "options": ai_response.get('options'),
        "complete": ai_response.get('complete', False),
        "summary": ai_response.get('summary'),
        "progress": {
            "current": session.current_question,
            "total": session.total_questions
        }
    }


@app.post("/chat/complete")
async def complete_chat_session(session_id: str):
    """
    Mark chat session as complete and get final intent
    """
    session = chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Generate final summary
    ai_response = await conversation_ai._generate_summary(session)
    
    session.completed = True
    
    return {
        "intent": ai_response['summary']['intent'],
        "context": ai_response['summary']['context'],
        "conversation_type": ai_response['summary']['conversation_type'],
        "message": "Chat completed successfully"
    }


@app.get("/chat/sessions")
async def list_chat_sessions(user_id: str = "default"):
    """List all chat sessions for a user"""
    sessions = [
        {
            "session_id": s.session_id,
            "created_at": s.created_at.isoformat(),
            "completed": s.completed,
            "message_count": len(s.messages),
            "conversation_type": s.conversation_type
        }
        for s in chat_manager.sessions.values()
        if s.user_id == user_id
    ]
    
    return {"sessions": sessions}


@app.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    chat_manager.delete_session(session_id)
    return {"message": "Session deleted"}


# ============== HEALTH CHECK ==============

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
