# 🚀 AI DevOps Assistant - Complete System Quick Start

## ✨ What You Have

A complete AI-powered DevOps assistant with:
- 🖥️ **Beautiful Web Interface** (Streamlit)
- 🧠 **4 Backend Microservices** (AI, RAG, MCP, Infrastructure)
- 🗄️ **Vector Database** (Qdrant)
- 📦 **Docker Deployment** (One command to rule them all)

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Prerequisites

```bash
# Install Docker and Docker Compose
# https://docs.docker.com/get-docker/

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Setup Environment

```bash
# Navigate to the directory
cd outputs

# Create .env file with your credentials
cat > .env << EOF
# Required: Claude AI API Key
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Required for deployments: AWS Credentials
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
EOF
```

### Step 3: Start Everything

```bash
# Start all services with frontend
docker-compose -f docker-compose-complete.yml up -d

# Wait for services to initialize (30 seconds)
sleep 30

# Seed the RAG service with AWS best practices
curl -X POST http://localhost:8002/seed
```

### Step 4: Access the Application

```bash
# Open the web interface
open http://localhost:8501

# Or manually go to:
# http://localhost:8501
```

That's it! 🎉

---

## 🎨 Using the Web Interface

### 1️⃣ Generate Infrastructure

1. Go to the **"Generate"** tab
2. Type your request in plain English:
   ```
   Create a VPC with 2 public and 2 private subnets
   ```
3. Click **"Generate Infrastructure"**
4. Review the Terraform code
5. Download if needed

### 2️⃣ Validate Infrastructure

1. Go to the **"Validate"** tab
2. Click **"Validate Infrastructure"**
3. Review:
   - 💰 Monthly cost estimate
   - 🔒 Security score
   - ⚠️ Issues and warnings
   - 💡 Recommendations
4. Fix critical issues if any

### 3️⃣ Deploy to AWS

1. Go to the **"Deploy"** tab
2. Enter deployment name
3. Check the confirmation box
4. Click **"Deploy to AWS"**
5. Watch progress in real-time
6. Celebrate! 🎊

---

## 📊 Service URLs

Once running, access these URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **🖥️ Frontend** | http://localhost:8501 | Web Interface |
| 🧠 AI Service | http://localhost:8001 | Code Generation |
| 📚 RAG Service | http://localhost:8002 | Best Practices |
| ⚡ MCP Service | http://localhost:8003 | Validation |
| 🚀 Infra Service | http://localhost:8004 | Deployment |
| 🗄️ Qdrant | http://localhost:6333 | Vector DB |

### API Documentation

- AI Service: http://localhost:8001/docs
- RAG Service: http://localhost:8002/docs
- MCP Service: http://localhost:8003/docs
- Infrastructure Service: http://localhost:8004/docs

---

## 🎯 Example Workflows

### Example 1: Simple VPC

**Request:**
```
Create a VPC with CIDR 10.0.0.0/16
```

**Result:**
- ✅ Terraform code generated
- 💰 Cost: ~$0/month (VPC is free)
- 🔒 Security: 100/100
- 🚀 Ready to deploy

---

### Example 2: Complete Network

**Request:**
```
Create a production VPC with 2 public and 2 private subnets
across 2 availability zones with NAT gateways
```

**Result:**
- ✅ Terraform code with VPC, subnets, IGW, NAT
- 💰 Cost: ~$65/month (NAT Gateway costs)
- 🔒 Security: 90/100
- 🚀 Ready to deploy

---

### Example 3: Web Application Stack

**Request:**
```
Set up infrastructure for a web application with load balancer,
3 EC2 instances, and RDS database
```

**Result:**
- ✅ Complete application infrastructure
- 💰 Cost: ~$350/month
- 🔒 Security: 85/100 (review encryption settings)
- 🚀 Review and deploy

---

## 🛠️ Useful Commands

### Check Service Status

```bash
# View all running services
docker-compose -f docker-compose-complete.yml ps

# Check logs for a specific service
docker logs ai-devops-frontend
docker logs ai-service
docker logs rag-service
docker logs mcp-service
docker logs infra-service

# Follow logs in real-time
docker logs -f ai-devops-frontend
```

### Restart Services

```bash
# Restart everything
docker-compose -f docker-compose-complete.yml restart

# Restart specific service
docker-compose -f docker-compose-complete.yml restart frontend
```

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose-complete.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose-complete.yml down -v
```

### Update Services

```bash
# Rebuild and restart
docker-compose -f docker-compose-complete.yml up -d --build
```

---

## 🐛 Troubleshooting

### Services Won't Start

**Problem:** `docker-compose up` fails

**Solution:**
```bash
# Check for port conflicts
lsof -i :8501  # Frontend
lsof -i :8001  # AI Service
lsof -i :8002  # RAG Service
lsof -i :8003  # MCP Service
lsof -i :8004  # Infrastructure Service

# Kill conflicting processes or change ports in docker-compose
```

---

### Frontend Shows "Service Unreachable"

**Problem:** All services show red in sidebar

**Solution:**
```bash
# Check if backend services are running
docker ps | grep -E "ai-service|rag-service|mcp-service|infra-service"

# Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Restart if needed
docker-compose -f docker-compose-complete.yml restart
```

---

### Code Generation Fails

**Problem:** "Failed to connect to AI Service"

**Solution:**
```bash
# Check if ANTHROPIC_API_KEY is set
docker exec ai-service env | grep ANTHROPIC_API_KEY

# View AI Service logs
docker logs ai-service

# If key is missing, update .env and restart
docker-compose -f docker-compose-complete.yml restart ai-service
```

---

### Deployment Fails

**Problem:** "Terraform apply failed"

**Solution:**
```bash
# Check if AWS credentials are set
docker exec infra-service env | grep AWS

# Check Infrastructure Service logs
docker logs infra-service

# Verify Terraform is installed
docker exec infra-service terraform version

# Test AWS access
docker exec infra-service aws sts get-caller-identity
```

---

### RAG Service Has No Data

**Problem:** Best practices not showing up

**Solution:**
```bash
# Seed the RAG service
curl -X POST http://localhost:8002/seed

# Verify documents were added
curl http://localhost:8002/stats

# Should show 12 documents
```

---

## 📚 Advanced Usage

### Using the API Directly

You can bypass the frontend and use the APIs directly:

```bash
# 1. Parse intent
curl -X POST http://localhost:8001/parse-intent \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a VPC"}'

# 2. Generate code
curl -X POST http://localhost:8001/generate-code \
  -H "Content-Type: application/json" \
  -d '{"intent": {...}, "rag_context": []}'

# 3. Validate
curl -X POST http://localhost:8003/validate \
  -H "Content-Type: application/json" \
  -d '{"terraform_code": "..."}'

# 4. Deploy
curl -X POST http://localhost:8004/deployments \
  -H "Content-Type: application/json" \
  -d '{"terraform_code": "...", "deployment_name": "my-vpc"}'
```

---

### Custom Configuration

Edit `docker-compose-complete.yml` to customize:

```yaml
# Change ports
ports:
  - "3000:8501"  # Frontend on port 3000

# Add resource limits
deploy:
  resources:
    limits:
      memory: 2G

# Add environment variables
environment:
  - CUSTOM_VAR=value
```

---

## 🎯 What's Included

### Frontend Features
- ✅ 3-step workflow (Generate → Validate → Deploy)
- ✅ Real-time service health monitoring
- ✅ Visual cost breakdown
- ✅ Security score display
- ✅ Deployment history tracking
- ✅ Syntax-highlighted code editor
- ✅ Download Terraform code
- ✅ Built-in documentation

### Backend Services
- ✅ AI Service: Claude AI integration for code generation
- ✅ RAG Service: Vector search with 12 pre-loaded AWS best practices
- ✅ MCP Service: Cost calculation, security validation, quota checking
- ✅ Infrastructure Service: Terraform deployment automation

---

## 🎊 Success Checklist

After setup, verify everything works:

- [ ] Frontend loads at http://localhost:8501
- [ ] All services show green in sidebar
- [ ] Can generate Terraform code
- [ ] Validation shows cost and security score
- [ ] (Optional) Can deploy to AWS

If all checked, you're good to go! 🚀

---

## 📞 Need Help?

1. Check service logs: `docker logs <service-name>`
2. Review API docs: http://localhost:8001/docs
3. Check troubleshooting section above
4. Verify all prerequisites are met

---

## 🎉 Next Steps

1. **Explore Examples** - Try different infrastructure requests
2. **Review Costs** - Always check before deploying
3. **Customize** - Modify services for your needs
4. **Deploy** - Create real AWS infrastructure
5. **Scale** - Run multiple instances for production

---

**Enjoy your AI DevOps Assistant!** 🚀

Transform natural language into cloud infrastructure with ease!
