"""API Gateway"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title="DevOps API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENTS = {
    "build": {"url": os.getenv("BUILD_AGENT_URL", "http://build-agent:8001"), "enabled": True},
    "github": {"url": os.getenv("GITHUB_AGENT_URL", "http://github-agent:8007"), "enabled": True},
    "docker": {"url": os.getenv("DOCKER_AGENT_URL", "http://docker-agent:8002"), "enabled": True},
}

@app.get("/")
async def root():
    return {"service": "DevOps API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health():
    results = {"gateway": "healthy", "agents": {}}
    async with httpx.AsyncClient() as client:
        for name, agent in AGENTS.items():
            if agent["enabled"]:
                try:
                    r = await client.get(f"{agent['url']}/health", timeout=3.0)
                    results["agents"][name] = {"status": "active", "health": "healthy" if r.status_code == 200 else "unhealthy"}
                except:
                    results["agents"][name] = {"status": "active", "health": "unreachable"}
    return results

@app.get("/agents")
async def list_agents():
    return {"agents": AGENTS}

# Orchestrated Build: Build Agent → Docker Agent
@app.post("/build-orchestrated")
async def orchestrated_build(request: Request):
    """
    Orchestrated build workflow:
    1. Build Agent: Analyze + Generate Dockerfile
    2. Docker Agent: Validate + Build Image
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        body = await request.json()
        project_path = body.get("project_path")
        image_name = body.get("image_name")
        tag = body.get("tag", "latest")
        
        logger.info(f"🚀 Starting orchestrated build for {image_name}:{tag}")
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            # Step 1: Build Agent - Generate Dockerfile
            logger.info("📊 Step 1: Calling Build Agent to generate Dockerfile...")
            build_response = await client.post(
                f"{AGENTS['build']['url']}/build",
                json={
                    "project_path": project_path,
                    "image_name": image_name,
                    "tag": tag
                }
            )
            
            if build_response.status_code != 200:
                return JSONResponse(
                    {"error": "Build Agent failed", "details": build_response.text},
                    status_code=500
                )
            
            build_result = build_response.json()
            build_job_id = build_result.get("job_id")
            logger.info(f"✅ Build Agent job created: {build_job_id}")
            
            # Wait for Dockerfile generation to complete
            import asyncio
            for i in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                status_response = await client.get(
                    f"{AGENTS['build']['url']}/build/{build_job_id}"
                )
                status = status_response.json()
                
                if status.get("status") == "completed":
                    logger.info("✅ Dockerfile generation completed")
                    dockerfile_path = f"{project_path}/Dockerfile"
                    break
                elif status.get("status") == "failed":
                    return JSONResponse(
                        {"error": "Dockerfile generation failed", "details": status.get("message")},
                        status_code=500
                    )
            else:
                return JSONResponse(
                    {"error": "Dockerfile generation timed out"},
                    status_code=500
                )
            
            # Step 2: Docker Agent - Build Image
            logger.info("🐳 Step 2: Calling Docker Agent to build image...")
            docker_response = await client.post(
                f"{AGENTS['docker']['url']}/build",
                json={
                    "dockerfilePath": dockerfile_path,
                    "imageName": image_name,
                    "tag": tag,
                    "validateBefore": True,
                    "validateAfter": True
                }
            )
            
            if docker_response.status_code != 200:
                return JSONResponse(
                    {"error": "Docker Agent failed", "details": docker_response.text},
                    status_code=500
                )
            
            docker_result = docker_response.json()
            logger.info(f"✅ Docker build started: {docker_result.get('job_id')}")
            
            return JSONResponse({
                "success": True,
                "build_job_id": build_job_id,
                "docker_job_id": docker_result.get("job_id"),
                "message": "Orchestrated build started",
                "workflow": {
                    "step1": "Dockerfile generated",
                    "step2": "Docker build in progress"
                }
            })
            
    except Exception as e:
        logger.error(f"❌ Orchestrated build failed: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

@app.api_route("/build/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_build(request: Request, path: str):
    return await proxy_request("build", path, request)


@app.api_route("/github/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_github(request: Request, path: str):
    return await proxy_request("github", path, request)

@app.api_route("/docker/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_docker(request: Request, path: str):
    return await proxy_request("docker", path, request)

async def proxy_request(agent_id: str, path: str, request: Request):
    agent = AGENTS.get(agent_id)
    if not agent or not agent["enabled"]:
        return JSONResponse({"error": "Agent not available"}, status_code=503)
    
    url = f"{agent['url']}/{path}"
    body = await request.body() if request.method in ["POST", "PUT"] else None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=dict(request.headers),
                content=body,
                timeout=30.0
            )
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code
            )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)