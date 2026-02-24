"""
GitHub Integration Service
Connects to GitHub to fetch projects, repositories, and code
"""

import os
import logging
from typing import Dict, List, Optional
import httpx
from datetime import datetime
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubIntegration:
    """
    GitHub Integration for fetching repositories and projects
    """
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv('GITHUB_ACCESS_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.access_token}" if self.access_token else None
        }
        
    async def get_user_info(self) -> Dict:
        """Get authenticated user information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    async def list_repositories(
        self,
        username: Optional[str] = None,
        sort: str = "updated",
        per_page: int = 30
    ) -> List[Dict]:
        """
        List repositories for a user
        
        Args:
            username: GitHub username (uses authenticated user if None)
            sort: Sort by 'created', 'updated', 'pushed', 'full_name'
            per_page: Number of results per page (max 100)
        """
        try:
            if username:
                url = f"{self.base_url}/users/{username}/repos"
            else:
                url = f"{self.base_url}/user/repos"
            
            params = {
                "sort": sort,
                "per_page": per_page
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                repos = response.json()
                
                # Format response
                return [{
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description"),
                    "private": repo["private"],
                    "clone_url": repo["clone_url"],
                    "ssh_url": repo["ssh_url"],
                    "html_url": repo["html_url"],
                    "language": repo.get("language"),
                    "default_branch": repo.get("default_branch", "main"),
                    "updated_at": repo["updated_at"],
                    "size": repo["size"]
                } for repo in repos]
                
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
            raise
    
    async def get_repository(self, owner: str, repo: str) -> Dict:
        """Get specific repository details"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}",
                    headers=self.headers
                )
                response.raise_for_status()
                repo_data = response.json()
                
                return {
                    "id": repo_data["id"],
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description"),
                    "private": repo_data["private"],
                    "clone_url": repo_data["clone_url"],
                    "ssh_url": repo_data["ssh_url"],
                    "html_url": repo_data["html_url"],
                    "language": repo_data.get("language"),
                    "default_branch": repo_data.get("default_branch", "main"),
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "size": repo_data["size"],
                    "stars": repo_data["stargazers_count"],
                    "forks": repo_data["forks_count"]
                }
        except Exception as e:
            logger.error(f"Failed to get repository: {e}")
            raise
    
    async def list_branches(self, owner: str, repo: str) -> List[Dict]:
        """List branches in a repository"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/branches",
                    headers=self.headers
                )
                response.raise_for_status()
                branches = response.json()
                
                return [{
                    "name": branch["name"],
                    "sha": branch["commit"]["sha"],
                    "protected": branch.get("protected", False)
                } for branch in branches]
        except Exception as e:
            logger.error(f"Failed to list branches: {e}")
            raise
    
    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        branch: Optional[str] = None
    ) -> Dict:
        """
        Get file content from repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            branch: Branch name (uses default branch if None)
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            params = {"ref": branch} if branch else {}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                file_data = response.json()
                
                # Decode base64 content
                if file_data.get("encoding") == "base64":
                    content = base64.b64decode(file_data["content"]).decode('utf-8')
                else:
                    content = file_data.get("content", "")
                
                return {
                    "name": file_data["name"],
                    "path": file_data["path"],
                    "sha": file_data["sha"],
                    "size": file_data["size"],
                    "content": content,
                    "download_url": file_data.get("download_url")
                }
        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            raise
    
    async def clone_repository(
        self,
        owner: str,
        repo: str,
        destination: str,
        branch: Optional[str] = None
    ) -> Dict:
        """
        Clone repository to local filesystem
        
        Args:
            owner: Repository owner
            repo: Repository name
            destination: Local path to clone into
            branch: Branch to clone (uses default if None)
        """
        try:
            import subprocess
            
            # Get repository info
            repo_info = await self.get_repository(owner, repo)
            clone_url = repo_info["clone_url"]
            branch = branch or repo_info["default_branch"]
            
            # Create destination directory
            os.makedirs(destination, exist_ok=True)
            
            # Clone command
            cmd = [
                "git", "clone",
                "--branch", branch,
                "--depth", "1",  # Shallow clone for speed
                clone_url,
                destination
            ]
            
            logger.info(f"Cloning {owner}/{repo} to {destination}")
            
            # Execute clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully cloned {owner}/{repo}")
                return {
                    "success": True,
                    "repository": f"{owner}/{repo}",
                    "branch": branch,
                    "destination": destination,
                    "message": f"Cloned to {destination}"
                }
            else:
                logger.error(f"❌ Clone failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    async def download_archive(
        self,
        owner: str,
        repo: str,
        destination: str,
        branch: Optional[str] = None,
        format: str = "zipball"
    ) -> Dict:
        """
        Download repository as archive (zip/tar)
        
        Args:
            owner: Repository owner
            repo: Repository name
            destination: Local path to save archive
            branch: Branch to download (uses default if None)
            format: 'zipball' or 'tarball'
        """
        try:
            # Get repository info
            repo_info = await self.get_repository(owner, repo)
            branch = branch or repo_info["default_branch"]
            
            url = f"{self.base_url}/repos/{owner}/{repo}/{format}/{branch}"
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                # Save to file
                filename = f"{repo}-{branch}.{'zip' if format == 'zipball' else 'tar.gz'}"
                filepath = os.path.join(destination, filename)
                
                os.makedirs(destination, exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Downloaded {owner}/{repo} to {filepath}")
                
                return {
                    "success": True,
                    "repository": f"{owner}/{repo}",
                    "branch": branch,
                    "filepath": filepath,
                    "size": len(response.content)
                }
                
        except Exception as e:
            logger.error(f"Failed to download archive: {e}")
            raise
    
    async def detect_project_type(self, owner: str, repo: str) -> Dict:
        """
        Detect project type by analyzing files in repository
        """
        try:
            # Common files to check
            files_to_check = [
                "package.json",      # Node.js
                "requirements.txt",  # Python
                "pom.xml",          # Java Maven
                "build.gradle",     # Java Gradle
                "go.mod",           # Go
                "Gemfile",          # Ruby
                "composer.json",    # PHP
                "Cargo.toml",       # Rust
                ".csproj"           # .NET
            ]
            
            detected = {
                "language": None,
                "framework": None,
                "package_manager": None,
                "files_found": []
            }
            
            for file in files_to_check:
                try:
                    content = await self.get_file_content(owner, repo, file)
                    detected["files_found"].append(file)
                    
                    # Detect based on file
                    if file == "package.json":
                        detected["language"] = "node"
                        detected["package_manager"] = "npm"
                        # Could parse package.json to detect framework
                    elif file == "requirements.txt":
                        detected["language"] = "python"
                        detected["package_manager"] = "pip"
                    elif file in ["pom.xml", "build.gradle"]:
                        detected["language"] = "java"
                        detected["package_manager"] = "maven" if file == "pom.xml" else "gradle"
                    elif file == "go.mod":
                        detected["language"] = "go"
                    elif file == "Gemfile":
                        detected["language"] = "ruby"
                        detected["package_manager"] = "bundler"
                    elif file == "composer.json":
                        detected["language"] = "php"
                        detected["package_manager"] = "composer"
                    elif file == "Cargo.toml":
                        detected["language"] = "rust"
                        detected["package_manager"] = "cargo"
                        
                except:
                    # File doesn't exist, continue
                    continue
            
            return detected
            
        except Exception as e:
            logger.error(f"Failed to detect project type: {e}")
            return {"language": None, "error": str(e)}


# OAuth Flow Helper
class GitHubOAuth:
    """Helper for GitHub OAuth flow"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
    
    def get_authorization_url(self, scope: str = "repo") -> str:
        """
        Get GitHub authorization URL
        
        Args:
            scope: OAuth scopes (e.g., 'repo', 'user', 'read:org')
        """
        return (
            f"{self.authorize_url}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scope}"
        )
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": self.redirect_uri
                    },
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Initialize
        github = GitHubIntegration(access_token="your-github-token")
        
        # List repositories
        repos = await github.list_repositories()
        print(f"Found {len(repos)} repositories")
        
        # Get specific repo
        if repos:
            repo = repos[0]
            owner, name = repo["full_name"].split("/")
            
            # Clone repository
            result = await github.clone_repository(
                owner=owner,
                repo=name,
                destination=f"/tmp/{name}"
            )
            print(result)
    
    asyncio.run(test())
