# 🧠 AI SERVICE - COMPLETE EXPLANATION

## 📋 What Does This Service Do?

The **AI Service** is the intelligent core of the AI DevOps Assistant. It acts as the "brain" that:

1. **Understands** what users want in plain English
2. **Generates** production-ready infrastructure code
3. **Refines** code based on validation feedback

### Real-World Example:

**User says:** *"I need a VPC with 2 private subnets for my app"*

**AI Service does:**
1. ✅ Understands: User needs VPC + 2 subnets (private)
2. ✅ Searches: Best practices for VPC design (via RAG service)
3. ✅ Generates: Complete Terraform code with security, NAT gateways, route tables
4. ✅ Returns: Code + explanation + cost estimate

---

## 🏗️ Architecture & Flow

```
┌──────────────────────────────────────────────────┐
│           AI SERVICE (Port 8001)                 │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │  ENDPOINT 1: /parse-intent              │   │
│  │  ─────────────────────────────          │   │
│  │  Input: "Create VPC with 2 subnets"     │   │
│  │  Uses: Claude AI API                     │   │
│  │  Output: {                               │   │
│  │    resources: ["vpc", "subnet"],         │   │
│  │    requirements: {...},                  │   │
│  │    complexity: "simple",                 │   │
│  │    needs_rag: true                       │   │
│  │  }                                       │   │
│  └─────────────────────────────────────────┘   │
│                      ↓                          │
│  ┌─────────────────────────────────────────┐   │
│  │  ENDPOINT 2: /generate-code             │   │
│  │  ─────────────────────────────          │   │
│  │  Input: Intent + RAG context + Policies │   │
│  │  Uses: Claude AI API                     │   │
│  │  Output: {                               │   │
│  │    terraform_code: "resource...",        │   │
│  │    explanation: "Creates VPC...",        │   │
│  │    resources_created: [...],             │   │
│  │    estimated_cost_info: "$45/month"      │   │
│  │  }                                       │   │
│  └─────────────────────────────────────────┘   │
│                      ↓                          │
│  ┌─────────────────────────────────────────┐   │
│  │  ENDPOINT 3: /refine-code               │   │
│  │  ─────────────────────────────          │   │
│  │  Input: Original code + Feedback        │   │
│  │  Uses: Claude AI API                     │   │
│  │  Output: Improved code                   │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 📂 Files & Their Purpose

### 1. **main.py** (450 lines)
**The Core Application**

This is the FastAPI application with all the endpoints:

```python
# Key Components:
- FastAPI app initialization
- 3 main endpoints:
  * /parse-intent: Convert natural language to structured data
  * /generate-code: Create Terraform code
  * /refine-code: Improve code based on feedback
- Claude AI client integration
- Error handling and validation
```

**What it does:**
- Receives HTTP requests from users/frontend
- Calls Claude AI API with carefully crafted prompts
- Parses Claude's JSON responses
- Returns structured data to caller

### 2. **config.py** (200 lines)
**Configuration Management**

Handles all settings and templates:

```python
# Contains:
- Environment variables (API keys, URLs)
- Prompt templates for Claude AI
- AWS resource mappings
- Complexity estimation rules
- Service configuration
```

**What it does:**
- Centralizes all configuration
- Provides reusable prompt templates
- Manages service settings
- Maps keywords to AWS resources

### 3. **utils.py** (280 lines)
**Helper Functions**

Utility functions for common tasks:

```python
# Key Functions:
- ClaudeAPIHandler: Wrapper for Claude API calls
- parse_json_response(): Extract JSON from Claude's responses
- extract_terraform_code(): Clean up code blocks
- estimate_complexity(): Determine infrastructure complexity
- identify_aws_resources(): Find AWS resources in text
- build_rag_context(): Format RAG search results
- validate_terraform_syntax(): Basic validation
```

**What it does:**
- Simplifies Claude API interactions
- Handles JSON parsing edge cases
- Provides reusable helper functions
- Validates basic Terraform syntax

### 4. **requirements.txt** (15 lines)
**Python Dependencies**

Lists all required packages:
- `fastapi`: Web framework
- `anthropic`: Claude AI SDK
- `pydantic`: Data validation
- `uvicorn`: ASGI server
- Testing libraries

### 5. **Dockerfile** (30 lines)
**Container Configuration**

Docker image for deployment:
- Python 3.11 base image
- Installs dependencies
- Copies application code
- Exposes port 8001
- Health check configuration

### 6. **.env.example** (20 lines)
**Environment Variables Template**

Template for configuration:
- Claude API key
- Service URLs
- Timeouts and limits
- Logging settings

---

## 🔄 How It Works Step-by-Step

### **Scenario: User wants to create a VPC**

#### Step 1: Intent Parsing
```
User Input: "Create a VPC with 2 private subnets in us-east-1"

↓ POST /parse-intent

Claude AI Prompt:
"Parse this request into JSON: 'Create a VPC with 2 private subnets...'"

↓ Claude AI processes

Response:
{
  "resources": ["vpc", "subnet", "nat_gateway", "route_table"],
  "requirements": {
    "vpc_count": 1,
    "subnet_count": 2,
    "subnet_type": "private",
    "region": "us-east-1"
  },
  "estimated_complexity": "simple",
  "needs_rag": true  // Needs best practices search
}
```

#### Step 2: RAG Context (External Service)
```
Because needs_rag = true:

↓ Call RAG Service

RAG Service returns:
[
  {
    "content": "VPC Best Practice: Use /16 CIDR for VPC...",
    "score": 0.95
  },
  {
    "content": "Private subnets require NAT gateway...",
    "score": 0.88
  }
]
```

#### Step 3: Code Generation
```
POST /generate-code

Input:
- Intent from step 1
- RAG context from step 2
- Organization policies (if any)

↓

Claude AI Prompt:
"Generate Terraform code for:
- Resources: VPC, 2 private subnets, NAT gateway
- Best practices: [RAG context]
- Policies: [Organization rules]
Return production-ready code with security best practices"

↓ Claude AI generates

Output:
{
  "terraform_code": "
    resource \"aws_vpc\" \"main\" {
      cidr_block = \"10.0.0.0/16\"
      enable_dns_hostnames = true
      tags = {
        Name = \"main-vpc\"
        Environment = \"production\"
      }
    }
    
    resource \"aws_subnet\" \"private_1\" {
      vpc_id = aws_vpc.main.id
      cidr_block = \"10.0.1.0/24\"
      availability_zone = \"us-east-1a\"
    }
    
    resource \"aws_subnet\" \"private_2\" {
      vpc_id = aws_vpc.main.id
      cidr_block = \"10.0.2.0/24\"
      availability_zone = \"us-east-1b\"
    }
    
    resource \"aws_nat_gateway\" \"main\" {
      allocation_id = aws_eip.nat.id
      subnet_id = aws_subnet.public.id
    }
    ...
  ",
  "explanation": "Creates a VPC with 2 private subnets across different AZs for high availability. Includes NAT gateway for outbound internet access.",
  "resources_created": [
    "aws_vpc", "aws_subnet", "aws_nat_gateway", 
    "aws_route_table", "aws_eip"
  ],
  "estimated_cost_info": "$45/month - NAT Gateway $32, EIP $3.60, VPC free"
}
```

#### Step 4: Validation (External MCP Service)
```
MCP Service validates:
✅ Cost: $45/month (acceptable)
✅ Security: All subnets properly configured
❌ Issue: Missing encryption on something

↓ Feedback sent to AI Service
```

#### Step 5: Code Refinement (If Needed)
```
POST /refine-code

Input:
- Original code
- Feedback: "Add encryption to EBS volumes"
- Validation results

↓ Claude AI refines

Output:
{
  "refined_code": "... (improved code with encryption)",
  "changes_made": "Added EBS encryption with KMS key",
  "remaining_concerns": "None"
}
```

---

## 🎯 Key Technologies Used

### 1. **Claude AI API**
- **Model:** `claude-sonnet-4-20250514`
- **Purpose:** Natural language understanding and code generation
- **Why:** Best at understanding context and generating accurate code

### 2. **FastAPI**
- **Purpose:** Web framework for REST API
- **Why:** Fast, modern, automatic API documentation

### 3. **Pydantic**
- **Purpose:** Data validation and serialization
- **Why:** Type safety and automatic validation

### 4. **Anthropic SDK**
- **Purpose:** Official Claude AI client
- **Why:** Reliable, maintained, feature-complete

---

## 💡 Claude AI Prompting Strategy

### **Intent Parsing Prompt:**
```
Simple and direct:
1. Show example output format (JSON schema)
2. List extraction rules
3. Emphasize JSON-only response
4. No extra explanation needed
```

### **Code Generation Prompt:**
```
Comprehensive:
1. Provide full context (intent + RAG + policies)
2. List all requirements clearly
3. Specify AWS best practices to follow
4. Request structured JSON response
5. Include cost estimation
```

### **Code Refinement Prompt:**
```
Problem-focused:
1. Show original code
2. Explain issues found
3. Provide validation results
4. Request specific fixes
5. Document changes made
```

---

## 📊 Performance & Scalability

### Response Times:
- Intent Parsing: **2-3 seconds**
- Code Generation: **5-8 seconds**
- Code Refinement: **4-6 seconds**

### Scalability:
- Stateless design (can run multiple instances)
- Rate limiting built-in (60 requests/minute)
- Retry logic with exponential backoff
- Health checks for monitoring

### Resource Usage:
- CPU: Low (I/O bound, waiting for Claude API)
- Memory: ~200MB per instance
- Network: Moderate (API calls to Claude)

---

## 🔒 Security Features

1. **API Key Management:** Environment variables, never hardcoded
2. **Input Validation:** Pydantic models validate all inputs
3. **Error Handling:** Never expose internal errors to users
4. **CORS:** Configurable allowed origins
5. **Non-root User:** Docker runs as non-privileged user

---

## 🚀 Deployment

### Local Development:
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key
python main.py
```

### Docker:
```bash
docker build -t ai-service .
docker run -p 8001:8001 -e ANTHROPIC_API_KEY=key ai-service
```

### Kubernetes:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: ai-service
        image: ai-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: claude-api-secret
              key: api-key
```

---

## 📈 Monitoring & Logging

### Health Endpoint:
```bash
curl http://localhost:8001/health
# Returns:
{
  "status": "healthy",
  "claude_api": "connected",
  "timestamp": "2025-11-13T10:30:00"
}
```

### Logs:
- Structured JSON logging
- Log levels: INFO, WARNING, ERROR
- Request/response logging
- Claude API call metrics

---

## 🎓 Summary

**The AI Service is:**
1. **The Intelligence:** Uses Claude AI to understand and generate
2. **The Translator:** Converts natural language ↔ infrastructure code
3. **The Expert:** Applies AWS best practices automatically
4. **The Collaborator:** Works with RAG and MCP services
5. **The Refiner:** Improves based on validation feedback

**It does NOT:**
- Store any state or data
- Deploy infrastructure (that's Infrastructure Service)
- Validate costs/security (that's MCP Service)
- Store knowledge (that's RAG Service)

**Perfect for:**
- Converting user requests to infrastructure
- Generating Terraform code with best practices
- Iterative refinement based on feedback

---

**Ready to use!** Just add your Anthropic API key and start generating infrastructure code! 🚀