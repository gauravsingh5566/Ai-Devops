"""
Docker Agent API
FastAPI endpoints for Docker operations with LLM validation
"""

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import logging
import uuid
from datetime import datetime

from docker_agent import DockerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Docker Agent API",
    description="Build and validate Docker images with AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Docker agent
docker_agent = DockerAgent()

# In-memory storage for jobs
docker_jobs = {}


# Request Models
class ValidateDockerfileRequest(BaseModel):
    dockerfile_content: str
    context: Optional[Dict] = None


class BuildImageRequest(BaseModel):
    dockerfile_path: str
    image_name: str
    tag: str = "latest"
    context_dir: Optional[str] = None
    build_args: Optional[Dict] = None
    validate_before_build: bool = True
    validate_after_build: bool = True


class ValidateImageRequest(BaseModel):
    image_name: str
    tag: str = "latest"


@app.get("/")
async def root():
    """Docker Agent information"""
    return {
        "service": "Docker Agent",
        "version": "1.0.0",
        "description": "Build and validate Docker images with AI",
        "features": [
            "Dockerfile validation with LLM",
            "Docker image building",
            "Built image validation",
            "Security scanning",
            "Optimization recommendations"
        ],
        "endpoints": {
            "validate_dockerfile": "POST /validate-dockerfile",
            "build": "POST /build",
            "validate_image": "POST /validate-image",
            "test_image": "POST /test-image",
            "jobs": "GET /jobs",
            "job_status": "GET /job/{job_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    llm_status = "enabled" if docker_agent.llm_model else "disabled"
    return {
        "status": "healthy",
        "llm_validation": llm_status
    }


@app.post("/validate-dockerfile")
async def validate_dockerfile(request: ValidateDockerfileRequest):
    """
    Validate Dockerfile using LLM
    
    Example:
    ```bash
    curl -X POST http://localhost:8002/validate-dockerfile \
      -H "Content-Type: application/json" \
      -d '{
        "dockerfile_content": "FROM python:3.11\\nCOPY . .",
        "context": {"language": "python", "framework": "fastapi"}
      }'
    ```
    """
    try:
        result = await docker_agent.validate_dockerfile(
            request.dockerfile_content,
            request.context
        )
        return result
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/build")
async def build_image(
    request: BuildImageRequest,
    background_tasks: BackgroundTasks
):
    """
    Build Docker image with optional validation
    
    Example:
    ```bash
    curl -X POST http://localhost:8002/build \
      -H "Content-Type: application/json" \
      -d '{
        "dockerfile_path": "/workspace/user/project/Dockerfile",
        "image_name": "my-app",
        "tag": "v1.0",
        "validate_before_build": true,
        "validate_after_build": true
      }'
    ```
    """
    job_id = str(uuid.uuid4())
    
    # Create job
    docker_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "image_name": request.image_name,
        "image_tag": request.tag,
        "validate_before": request.validate_before_build,
        "validate_after": request.validate_after_build
    }
    
    # Run build in background
    background_tasks.add_task(
        run_docker_build,
        job_id,
        request
    )
    
    return docker_jobs[job_id]


@app.post("/validate-image")
async def validate_image(request: ValidateImageRequest):
    """
    Validate a built Docker image
    
    Example:
    ```bash
    curl -X POST http://localhost:8002/validate-image \
      -H "Content-Type: application/json" \
      -d '{
        "image_name": "my-app",
        "tag": "latest"
      }'
    ```
    """
    try:
        result = await docker_agent.validate_image(
            request.image_name,
            request.tag
        )
        return result
    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-image")
async def test_image(request: ValidateImageRequest):
    """
    Test if Docker image can run
    
    Example:
    ```bash
    curl -X POST http://localhost:8002/test-image \
      -H "Content-Type: application/json" \
      -d '{
        "image_name": "my-app",
        "tag": "latest"
      }'
    ```
    """
    try:
        result = await docker_agent.test_image(
            request.image_name,
            request.tag
        )
        return result
    except Exception as e:
        logger.error(f"Image test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get Docker build job status"""
    if job_id not in docker_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return docker_jobs[job_id]


@app.get("/jobs")
async def list_jobs(limit: int = 20):
    """List recent Docker build jobs"""
    jobs = list(docker_jobs.values())[-limit:]
    return {
        "count": len(jobs),
        "jobs": jobs
    }


async def run_docker_build(job_id: str, request: BuildImageRequest):
    """Run Docker build process with validation"""
    
    try:
        # Step 1: Validate Dockerfile before build (if requested)
        if request.validate_before_build:
            docker_jobs[job_id]["status"] = "validating_dockerfile"
            logger.info(f"[{job_id}] Validating Dockerfile...")
            
            # Read Dockerfile
            try:
                with open(request.dockerfile_path, 'r') as f:
                    dockerfile_content = f.read()
                
                validation = await docker_agent.validate_dockerfile(
                    dockerfile_content
                )
                
                docker_jobs[job_id]["dockerfile_validation"] = validation
                
                # Check for critical issues
                critical_issues = [
                    issue for issue in validation.get("issues", [])
                    if issue.get("severity") == "CRITICAL"
                ]
                
                if critical_issues:
                    docker_jobs[job_id]["status"] = "failed"
                    docker_jobs[job_id]["error"] = "Critical issues found in Dockerfile"
                    docker_jobs[job_id]["critical_issues"] = critical_issues
                    logger.error(f"[{job_id}] Critical issues found, aborting build")
                    return
                
                logger.info(f"[{job_id}] Dockerfile validation passed")
                
            except FileNotFoundError:
                docker_jobs[job_id]["status"] = "failed"
                docker_jobs[job_id]["error"] = f"Dockerfile not found: {request.dockerfile_path}"
                return
        
        # Step 2: Build Docker image
        docker_jobs[job_id]["status"] = "building"
        logger.info(f"[{job_id}] Building Docker image...")
        
        build_result = await docker_agent.build_image(
            dockerfile_path=request.dockerfile_path,
            image_name=request.image_name,
            tag=request.tag,
            context_dir=request.context_dir,
            build_args=request.build_args
        )
        
        # Update job with build results
        docker_jobs[job_id].update(build_result)
        
        if not build_result["success"]:
            docker_jobs[job_id]["status"] = "failed"
            logger.error(f"[{job_id}] Build failed")
            return
        
        logger.info(f"[{job_id}] Build successful")
        
        # Step 3: Validate built image (if requested)
        if request.validate_after_build:
            docker_jobs[job_id]["status"] = "validating_image"
            logger.info(f"[{job_id}] Validating built image...")
            
            image_validation = await docker_agent.validate_image(
                request.image_name,
                request.tag
            )
            
            docker_jobs[job_id]["image_validation"] = image_validation
            logger.info(f"[{job_id}] Image validation complete")
            
            # Step 4: Test image
            docker_jobs[job_id]["status"] = "testing"
            logger.info(f"[{job_id}] Testing image...")
            
            test_result = await docker_agent.test_image(
                request.image_name,
                request.tag
            )
            
            docker_jobs[job_id]["image_test"] = test_result
        
        # Complete
        docker_jobs[job_id]["status"] = "completed"
        docker_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[{job_id}] ✅ All steps completed successfully")
        
    except Exception as e:
        logger.error(f"[{job_id}] Error: {e}")
        docker_jobs[job_id]["status"] = "failed"
        docker_jobs[job_id]["error"] = str(e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
