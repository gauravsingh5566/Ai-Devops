"""
GitHub Agent - Project Import and Management
Allows users to connect GitHub and import projects for building
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

sys.path.append('/app/shared')
from github_integration import GitHubIntegration
from database import mongodb, get_collection, Collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubAgent:
    """
    GitHub Agent for managing project imports from GitHub
    """
    
    def __init__(self):
        self.workspace_dir = os.getenv('WORKSPACE_DIR', '/workspace')
        os.makedirs(self.workspace_dir, exist_ok=True)
        
    async def connect_github_account(self, user_id: str, access_token: str) -> Dict:
        """
        Connect user's GitHub account and save credentials
        
        Args:
            user_id: Internal user ID
            access_token: GitHub personal access token
            
        Returns:
            Connection status and user info
        """
        try:
            # Initialize GitHub client
            github = GitHubIntegration(access_token=access_token)
            
            # Get GitHub user info
            user_info = await github.get_user_info()
            
            # Save to database
            await mongodb.connect()
            users_collection = await get_collection(Collections.USERS)
            
            await users_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "github": {
                            "connected": True,
                            "username": user_info["login"],
                            "name": user_info.get("name"),
                            "email": user_info.get("email"),
                            "avatar_url": user_info.get("avatar_url"),
                            "access_token": access_token,  # In production, encrypt this!
                            "connected_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ GitHub account connected for user {user_id}")
            
            return {
                "success": True,
                "github_username": user_info["login"],
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "avatar_url": user_info.get("avatar_url"),
                "public_repos": user_info.get("public_repos"),
                "message": "GitHub account connected successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to connect GitHub account: {e}")
            raise
    
    async def get_user_repositories(
        self,
        user_id: str,
        refresh: bool = False
    ) -> List[Dict]:
        """
        Get user's GitHub repositories
        
        Args:
            user_id: Internal user ID
            refresh: Force refresh from GitHub API
            
        Returns:
            List of repositories
        """
        try:
            await mongodb.connect()
            users_collection = await get_collection(Collections.USERS)
            projects_collection = await get_collection(Collections.PROJECTS)
            
            # Get user's GitHub credentials
            user = await users_collection.find_one({"user_id": user_id})
            
            if not user or not user.get("github", {}).get("connected"):
                raise Exception("GitHub account not connected")
            
            access_token = user["github"]["access_token"]
            github = GitHubIntegration(access_token=access_token)
            
            # Get repositories from GitHub
            repos = await github.list_repositories(sort="updated", per_page=100)
            
            # Save/update in database
            for repo in repos:
                await projects_collection.update_one(
                    {
                        "user_id": user_id,
                        "source": "github",
                        "github_id": repo["id"]
                    },
                    {
                        "$set": {
                            "user_id": user_id,
                            "source": "github",
                            "github_id": repo["id"],
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                            "description": repo.get("description"),
                            "language": repo.get("language"),
                            "clone_url": repo["clone_url"],
                            "html_url": repo["html_url"],
                            "default_branch": repo["default_branch"],
                            "private": repo["private"],
                            "updated_at": repo["updated_at"],
                            "last_synced": datetime.utcnow().isoformat()
                        }
                    },
                    upsert=True
                )
            
            logger.info(f"✅ Synced {len(repos)} repositories for user {user_id}")
            
            return repos
            
        except Exception as e:
            logger.error(f"Failed to get repositories: {e}")
            raise
    
    async def import_project(
        self,
        user_id: str,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> Dict:
        """
        Import a project from GitHub for building
        
        Args:
            user_id: Internal user ID
            owner: Repository owner
            repo: Repository name
            branch: Branch to import (uses default if None)
            
        Returns:
            Import status and project details
        """
        try:
            await mongodb.connect()
            users_collection = await get_collection(Collections.USERS)
            projects_collection = await get_collection(Collections.PROJECTS)
            
            # Get user's GitHub credentials
            user = await users_collection.find_one({"user_id": user_id})
            
            if not user or not user.get("github", {}).get("connected"):
                raise Exception("GitHub account not connected")
            
            access_token = user["github"]["access_token"]
            github = GitHubIntegration(access_token=access_token)
            
            # Get repository info
            repo_info = await github.get_repository(owner, repo)
            branch = branch or repo_info["default_branch"]
            
            # Create workspace directory for this project
            project_dir = os.path.join(
                self.workspace_dir,
                user_id,
                f"{owner}-{repo}"
            )
            
            # Clone repository
            logger.info(f"Cloning {owner}/{repo} to {project_dir}")
            clone_result = await github.clone_repository(
                owner=owner,
                repo=repo,
                destination=project_dir,
                branch=branch
            )
            
            if not clone_result["success"]:
                raise Exception(f"Clone failed: {clone_result.get('error')}")
            
            # Detect project type
            detection = await github.detect_project_type(owner, repo)
            
            # Save project to database
            project_data = {
                "user_id": user_id,
                "source": "github",
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "branch": branch,
                "local_path": project_dir,
                "language": detection.get("language"),
                "framework": detection.get("framework"),
                "package_manager": detection.get("package_manager"),
                "clone_url": repo_info["clone_url"],
                "html_url": repo_info["html_url"],
                "imported": True,
                "imported_at": datetime.utcnow().isoformat(),
                "status": "ready",
                "metadata": {
                    "description": repo_info.get("description"),
                    "stars": repo_info.get("stars"),
                    "language": repo_info.get("language"),
                    "size": repo_info.get("size")
                }
            }
            
            result = await projects_collection.update_one(
                {
                    "user_id": user_id,
                    "source": "github",
                    "full_name": f"{owner}/{repo}"
                },
                {"$set": project_data},
                upsert=True
            )
            
            logger.info(f"✅ Project {owner}/{repo} imported successfully")
            
            return {
                "success": True,
                "project": {
                    "full_name": f"{owner}/{repo}",
                    "branch": branch,
                    "local_path": project_dir,
                    "language": detection.get("language"),
                    "framework": detection.get("framework"),
                    "status": "ready"
                },
                "message": f"Project imported and ready to build"
            }
            
        except Exception as e:
            logger.error(f"Failed to import project: {e}")
            raise
    
    async def get_imported_projects(self, user_id: str) -> List[Dict]:
        """
        Get user's imported projects
        
        Args:
            user_id: Internal user ID
            
        Returns:
            List of imported projects
        """
        try:
            await mongodb.connect()
            projects_collection = await get_collection(Collections.PROJECTS)
            
            cursor = projects_collection.find({
                "user_id": user_id,
                "imported": True
            }).sort("imported_at", -1)
            
            projects = []
            async for project in cursor:
                # Convert ObjectId to string
                project["_id"] = str(project["_id"])
                projects.append(project)
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get imported projects: {e}")
            raise
    
    async def sync_project(
        self,
        user_id: str,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> Dict:
        """
        Sync/update an imported project with latest changes from GitHub
        
        Args:
            user_id: Internal user ID
            owner: Repository owner
            repo: Repository name
            branch: Branch to sync
            
        Returns:
            Sync status
        """
        try:
            await mongodb.connect()
            projects_collection = await get_collection(Collections.PROJECTS)
            
            # Get project from database
            project = await projects_collection.find_one({
                "user_id": user_id,
                "full_name": f"{owner}/{repo}"
            })
            
            if not project:
                raise Exception("Project not found")
            
            project_dir = project["local_path"]
            
            # Pull latest changes
            import subprocess
            
            logger.info(f"Syncing {owner}/{repo} at {project_dir}")
            
            result = subprocess.run(
                ["git", "pull"],
                cwd=project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Update sync timestamp
                await projects_collection.update_one(
                    {"_id": project["_id"]},
                    {"$set": {"last_synced": datetime.utcnow().isoformat()}}
                )
                
                logger.info(f"✅ Project {owner}/{repo} synced successfully")
                
                return {
                    "success": True,
                    "message": "Project synced with latest changes",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to sync project: {e}")
            raise
    
    async def delete_imported_project(
        self,
        user_id: str,
        owner: str,
        repo: str
    ) -> Dict:
        """
        Delete an imported project
        
        Args:
            user_id: Internal user ID
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Deletion status
        """
        try:
            await mongodb.connect()
            projects_collection = await get_collection(Collections.PROJECTS)
            
            # Get project
            project = await projects_collection.find_one({
                "user_id": user_id,
                "full_name": f"{owner}/{repo}"
            })
            
            if not project:
                raise Exception("Project not found")
            
            # Delete local files
            import shutil
            if os.path.exists(project["local_path"]):
                shutil.rmtree(project["local_path"])
            
            # Remove from database
            await projects_collection.delete_one({"_id": project["_id"]})
            
            logger.info(f"✅ Project {owner}/{repo} deleted")
            
            return {
                "success": True,
                "message": f"Project {owner}/{repo} deleted"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            raise


# Example usage
if __name__ == "__main__":
    async def test():
        agent = GitHubAgent()
        
        # Connect GitHub account
        result = await agent.connect_github_account(
            user_id="user123",
            access_token="ghp_your_token_here"
        )
        print("Connected:", result)
        
        # Get repositories
        repos = await agent.get_user_repositories(user_id="user123")
        print(f"Found {len(repos)} repositories")
        
        # Import a project
        if repos:
            repo = repos[0]
            owner, name = repo["full_name"].split("/")
            
            import_result = await agent.import_project(
                user_id="user123",
                owner=owner,
                repo=name
            )
            print("Imported:", import_result)
    
    asyncio.run(test())
