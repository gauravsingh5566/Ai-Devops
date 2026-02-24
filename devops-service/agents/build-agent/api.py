"""Build Agent API"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid
import logging
from datetime import datetime
from build_agent import BuildAgent

logger = logging.getLogger(__name__)

app = FastAPI(title="Build Agent API")
build_agent = BuildAgent()
build_jobs = {}

class BuildRequest(BaseModel):
    project_path: str
    image_name: str
    tag: str = "latest"
    optimize: bool = True

@app.get("/")
async def root():
    return {"service": "Build Agent", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze(request: dict):
    project_info = await build_agent.analyze_project(request['project_path'])
    return {"success": True, "project_info": project_info}

@app.post("/build")
async def build(request: BuildRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    build_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "image_name": request.image_name,
        "image_tag": request.tag
    }
    background_tasks.add_task(run_build, job_id, request)
    return build_jobs[job_id]

@app.get("/build/{job_id}")
async def get_build(job_id: str):
    if job_id not in build_jobs:
        raise HTTPException(404, "Job not found")
    return build_jobs[job_id]

@app.get("/builds")
async def list_builds(limit: int = 10):
    return list(build_jobs.values())[-limit:]

async def run_build(job_id: str, request: BuildRequest):
    """
    Build Agent: Analyze project and generate Dockerfile
    Does NOT build the Docker image - that's Docker Agent's job!
    """
    try:
        logger.info(f"🚀 Starting Dockerfile generation job {job_id}")
        
        # Step 1: Analyze project
        build_jobs[job_id]["status"] = "analyzing"
        logger.info(f"📊 Analyzing project: {request.project_path}")
        project_info = await build_agent.analyze_project(request.project_path)
        build_jobs[job_id]["project_info"] = project_info
        logger.info(f"✅ Analysis complete: {project_info.get('language')}/{project_info.get('framework')}")
        
        # Step 2: Generate Dockerfile
        build_jobs[job_id]["status"] = "generating_dockerfile"
        logger.info("🤖 Generating Dockerfile with AI...")
        dockerfile = build_agent.generate_dockerfile(project_info)
        build_jobs[job_id]["dockerfile"] = dockerfile
        logger.info(f"✅ Dockerfile generated ({len(dockerfile) if dockerfile else 0} chars)")
        
        # Step 3: Save Dockerfile to project directory
        build_jobs[job_id]["status"] = "saving_dockerfile"
        logger.info(f"💾 Saving Dockerfile to {request.project_path}")
        success, message = await build_agent.save_dockerfile(
            request.project_path,
            dockerfile,
            project_info
        )
        
        if success:
            logger.info(f"✅ Dockerfile saved successfully")
            build_jobs[job_id]["status"] = "completed"
            build_jobs[job_id]["message"] = "Dockerfile generated and saved"
            build_jobs[job_id]["dockerfile_path"] = f"{request.project_path}/Dockerfile"
        else:
            logger.error(f"❌ Failed to save Dockerfile: {message}")
            build_jobs[job_id]["status"] = "failed"
            build_jobs[job_id]["message"] = f"Failed to save Dockerfile: {message}"
        
        build_jobs[job_id]["success"] = success
        build_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"🏁 Dockerfile generation job {job_id} finished: {build_jobs[job_id]['status']}")
        
    except Exception as e:
        logger.error(f"❌ Dockerfile generation job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()
        build_jobs[job_id]["status"] = "failed"
        build_jobs[job_id]["message"] = str(e)
        build_jobs[job_id]["error"] = traceback.format_exc()
        build_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)