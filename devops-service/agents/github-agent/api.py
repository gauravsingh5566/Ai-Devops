"""
GitHub Agent API
API endpoints for GitHub integration and project import
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging

from github_agent import GitHubAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GitHub Agent API",
    description="Connect GitHub and import projects for building",
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

# Initialize GitHub agent
github_agent = GitHubAgent()


# Request Models
class ConnectGitHubRequest(BaseModel):
    access_token: str

class ImportProjectRequest(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = None

class SyncProjectRequest(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = None


# Helper to get user_id from header
def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Get user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID header required")
    return x_user_id


@app.get("/")
async def root():
    """GitHub Agent information"""
    return {
        "service": "GitHub Agent",
        "version": "1.0.0",
        "description": "Connect GitHub and import projects",
        "endpoints": {
            "connect": "POST /github/connect",
            "repositories": "GET /github/repos",
            "import": "POST /github/import",
            "projects": "GET /github/projects",
            "sync": "POST /github/sync"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}


# Add routes without /github prefix (for API gateway compatibility)
@app.post("/connect")
async def connect_github_direct(
    request: ConnectGitHubRequest,
    x_user_id: str = Header(...)
):
    """Connect GitHub (direct route for gateway)"""
    return await connect_github(request, x_user_id)


@app.post("/github/connect")
async def connect_github(
    request: ConnectGitHubRequest,
    x_user_id: str = Header(...)
):
    """
    Connect user's GitHub account
    
    Headers:
    - X-User-ID: User identifier
    
    Body:
    - access_token: GitHub personal access token
    
    Example:
    ```bash
    curl -X POST http://localhost:8007/github/connect \
      -H "X-User-ID: user123" \
      -H "Content-Type: application/json" \
      -d '{"access_token": "ghp_your_token"}'
    ```
    """
    try:
        result = await github_agent.connect_github_account(
            user_id=x_user_id,
            access_token=request.access_token
        )
        return result
    except Exception as e:
        logger.error(f"Failed to connect GitHub: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/repos")
async def get_repositories_direct(
    refresh: bool = False,
    x_user_id: str = Header(...)
):
    """Get repositories (direct route for gateway)"""
    return await get_repositories(refresh, x_user_id)


@app.get("/github/repos")
async def get_repositories(
    refresh: bool = False,
    x_user_id: str = Header(...)
):
    """
    Get user's GitHub repositories
    
    Headers:
    - X-User-ID: User identifier
    
    Query Parameters:
    - refresh: Force refresh from GitHub API (default: false)
    
    Example:
    ```bash
    curl http://localhost:8007/github/repos \
      -H "X-User-ID: user123"
    ```
    """
    try:
        repos = await github_agent.get_user_repositories(
            user_id=x_user_id,
            refresh=refresh
        )
        return {
            "success": True,
            "count": len(repos),
            "repositories": repos
        }
    except Exception as e:
        logger.error(f"Failed to get repositories: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/import")
async def import_project_direct(
    request: ImportProjectRequest,
    x_user_id: str = Header(...)
):
    """Import project (direct route for gateway)"""
    return await import_project(request, x_user_id)


@app.post("/github/import")
async def import_project(
    request: ImportProjectRequest,
    x_user_id: str = Header(...)
):
    """
    Import a GitHub project for building
    
    Headers:
    - X-User-ID: User identifier
    
    Body:
    - owner: Repository owner (GitHub username)
    - repo: Repository name
    - branch: Branch to import (optional, uses default branch)
    
    Example:
    ```bash
    curl -X POST http://localhost:8007/github/import \
      -H "X-User-ID: user123" \
      -H "Content-Type: application/json" \
      -d '{
        "owner": "username",
        "repo": "my-project",
        "branch": "main"
      }'
    ```
    """
    try:
        result = await github_agent.import_project(
            user_id=x_user_id,
            owner=request.owner,
            repo=request.repo,
            branch=request.branch
        )
        return result
    except Exception as e:
        logger.error(f"Failed to import project: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/projects")
async def get_projects_direct(x_user_id: str = Header(...)):
    """Get projects (direct route for gateway)"""
    return await get_projects(x_user_id)


@app.get("/github/projects")
async def get_projects(x_user_id: str = Header(...)):
    """
    Get user's imported projects
    
    Headers:
    - X-User-ID: User identifier
    
    Example:
    ```bash
    curl http://localhost:8007/github/projects \
      -H "X-User-ID: user123"
    ```
    """
    try:
        projects = await github_agent.get_imported_projects(user_id=x_user_id)
        return {
            "success": True,
            "count": len(projects),
            "projects": projects
        }
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/github/sync")
async def sync_project(
    request: SyncProjectRequest,
    x_user_id: str = Header(...)
):
    """
    Sync/update an imported project with latest changes
    
    Headers:
    - X-User-ID: User identifier
    
    Body:
    - owner: Repository owner
    - repo: Repository name
    - branch: Branch to sync (optional)
    
    Example:
    ```bash
    curl -X POST http://localhost:8007/github/sync \
      -H "X-User-ID: user123" \
      -H "Content-Type: application/json" \
      -d '{
        "owner": "username",
        "repo": "my-project"
      }'
    ```
    """
    try:
        result = await github_agent.sync_project(
            user_id=x_user_id,
            owner=request.owner,
            repo=request.repo,
            branch=request.branch
        )
        return result
    except Exception as e:
        logger.error(f"Failed to sync project: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/github/projects/{owner}/{repo}")
async def delete_project(
    owner: str,
    repo: str,
    x_user_id: str = Header(...)
):
    """
    Delete an imported project
    
    Headers:
    - X-User-ID: User identifier
    
    Path Parameters:
    - owner: Repository owner
    - repo: Repository name
    
    Example:
    ```bash
    curl -X DELETE http://localhost:8007/github/projects/username/my-project \
      -H "X-User-ID: user123"
    ```
    """
    try:
        result = await github_agent.delete_imported_project(
            user_id=x_user_id,
            owner=owner,
            repo=repo
        )
        return result
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)