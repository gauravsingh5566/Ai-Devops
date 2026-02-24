"""
GitHub Integration API
API endpoints for GitHub repository integration
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import logging

import sys
sys.path.append('/app/shared')
from github_integration import GitHubIntegration, GitHubOAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GitHub Integration API",
    description="Connect and fetch projects from GitHub",
    version="1.0.0"
)

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/github/callback")

oauth = GitHubOAuth(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri=GITHUB_REDIRECT_URI
)


# Request/Response Models
class ConnectGitHubRequest(BaseModel):
    access_token: str

class CloneRepositoryRequest(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = None
    destination: Optional[str] = "/workspace"

class DownloadArchiveRequest(BaseModel):
    owner: str
    repo: str
    branch: Optional[str] = None
    format: str = "zipball"  # zipball or tarball


# Dependency to get GitHub client
async def get_github_client(
    access_token: str = Query(..., description="GitHub access token")
) -> GitHubIntegration:
    """Get GitHub integration client"""
    return GitHubIntegration(access_token=access_token)


@app.get("/")
async def root():
    """API information"""
    return {
        "service": "GitHub Integration API",
        "version": "1.0.0",
        "endpoints": {
            "oauth": "/github/auth",
            "repos": "/github/repos",
            "clone": "/github/clone",
            "download": "/github/download"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


# OAuth Flow
@app.get("/github/auth")
async def github_auth():
    """
    Start GitHub OAuth flow
    Redirects user to GitHub authorization page
    """
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET"
        )
    
    auth_url = oauth.get_authorization_url(scope="repo,user")
    return RedirectResponse(url=auth_url)


@app.get("/github/callback")
async def github_callback(code: str):
    """
    GitHub OAuth callback
    Exchanges code for access token
    """
    try:
        token_data = await oauth.exchange_code_for_token(code)
        
        return {
            "success": True,
            "access_token": token_data.get("access_token"),
            "token_type": token_data.get("token_type"),
            "scope": token_data.get("scope"),
            "message": "Successfully authenticated with GitHub"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Repository Endpoints
@app.get("/github/user")
async def get_user(github: GitHubIntegration = Depends(get_github_client)):
    """
    Get authenticated GitHub user information
    
    Query Parameters:
    - access_token: GitHub personal access token
    """
    try:
        user_info = await github.get_user_info()
        return {
            "success": True,
            "user": {
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "avatar_url": user_info.get("avatar_url"),
                "bio": user_info.get("bio"),
                "public_repos": user_info.get("public_repos"),
                "followers": user_info.get("followers"),
                "following": user_info.get("following")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/github/repos")
async def list_repositories(
    username: Optional[str] = None,
    sort: str = Query("updated", description="Sort by: created, updated, pushed, full_name"),
    per_page: int = Query(30, ge=1, le=100),
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    List GitHub repositories
    
    Query Parameters:
    - access_token: GitHub personal access token (required)
    - username: GitHub username (optional, uses authenticated user if not provided)
    - sort: Sort order (created, updated, pushed, full_name)
    - per_page: Results per page (1-100)
    """
    try:
        repos = await github.list_repositories(
            username=username,
            sort=sort,
            per_page=per_page
        )
        
        return {
            "success": True,
            "count": len(repos),
            "repositories": repos
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/github/repos/{owner}/{repo}")
async def get_repository(
    owner: str,
    repo: str,
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    Get specific repository details
    
    Path Parameters:
    - owner: Repository owner
    - repo: Repository name
    
    Query Parameters:
    - access_token: GitHub personal access token
    """
    try:
        repo_info = await github.get_repository(owner, repo)
        return {
            "success": True,
            "repository": repo_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/github/repos/{owner}/{repo}/branches")
async def list_branches(
    owner: str,
    repo: str,
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    List branches in a repository
    
    Path Parameters:
    - owner: Repository owner
    - repo: Repository name
    
    Query Parameters:
    - access_token: GitHub personal access token
    """
    try:
        branches = await github.list_branches(owner, repo)
        return {
            "success": True,
            "count": len(branches),
            "branches": branches
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/github/repos/{owner}/{repo}/detect")
async def detect_project_type(
    owner: str,
    repo: str,
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    Detect project type (language, framework) by analyzing repository files
    
    Path Parameters:
    - owner: Repository owner
    - repo: Repository name
    
    Query Parameters:
    - access_token: GitHub personal access token
    """
    try:
        detection = await github.detect_project_type(owner, repo)
        return {
            "success": True,
            "repository": f"{owner}/{repo}",
            "detection": detection
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/github/clone")
async def clone_repository(
    request: CloneRepositoryRequest,
    access_token: str = Query(...),
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    Clone a GitHub repository to local filesystem
    
    Request Body:
    - owner: Repository owner
    - repo: Repository name
    - branch: Branch to clone (optional)
    - destination: Local path (optional, defaults to /workspace)
    
    Query Parameters:
    - access_token: GitHub personal access token
    """
    try:
        result = await github.clone_repository(
            owner=request.owner,
            repo=request.repo,
            destination=request.destination,
            branch=request.branch
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/github/download")
async def download_archive(
    request: DownloadArchiveRequest,
    access_token: str = Query(...),
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    Download repository as ZIP or TAR archive
    
    Request Body:
    - owner: Repository owner
    - repo: Repository name
    - branch: Branch to download (optional)
    - format: 'zipball' or 'tarball' (default: zipball)
    
    Query Parameters:
    - access_token: GitHub personal access token
    """
    try:
        result = await github.download_archive(
            owner=request.owner,
            repo=request.repo,
            destination="/workspace",
            branch=request.branch,
            format=request.format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/github/repos/{owner}/{repo}/file/{path:path}")
async def get_file(
    owner: str,
    repo: str,
    path: str,
    branch: Optional[str] = None,
    github: GitHubIntegration = Depends(get_github_client)
):
    """
    Get file content from repository
    
    Path Parameters:
    - owner: Repository owner
    - repo: Repository name
    - path: File path in repository
    
    Query Parameters:
    - access_token: GitHub personal access token
    - branch: Branch name (optional)
    """
    try:
        file_content = await github.get_file_content(owner, repo, path, branch)
        return {
            "success": True,
            "file": file_content
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
