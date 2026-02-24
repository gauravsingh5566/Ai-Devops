# 🔗 GitHub Agent - Project Import Service

**Connect GitHub and import projects for automated building**

---

## 🎯 Features

✅ **GitHub OAuth** - Connect user accounts securely  
✅ **Repository Listing** - Browse all user repositories  
✅ **Project Import** - Clone projects to workspace  
✅ **Auto-Detection** - Detect language & framework  
✅ **Project Sync** - Pull latest changes  
✅ **Project Management** - List, sync, delete projects  

---

## 🚀 Quick Start

### 1. Start Service

```bash
# Standalone
python api.py

# Docker
docker build -t github-agent .
docker run -p 8007:8007 \
  -v /workspace:/workspace \
  -e MONGODB_URL=mongodb://... \
  github-agent
```

### 2. Connect GitHub

```bash
curl -X POST http://localhost:8007/github/connect \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "ghp_your_github_token"}'
```

### 3. List Repositories

```bash
curl http://localhost:8007/github/repos \
  -H "X-User-ID: user123"
```

### 4. Import Project

```bash
curl -X POST http://localhost:8007/github/import \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "username",
    "repo": "my-app",
    "branch": "main"
  }'
```

---

## 📡 API Endpoints

### POST /github/connect
**Connect GitHub account**

Headers:
- `X-User-ID: user123`

Body:
```json
{
  "access_token": "ghp_your_token"
}
```

Response:
```json
{
  "success": true,
  "github_username": "username",
  "name": "Full Name",
  "email": "email@example.com",
  "avatar_url": "https://...",
  "public_repos": 42
}
```

---

### GET /github/repos
**List user's repositories**

Headers:
- `X-User-ID: user123`

Query:
- `refresh=true` - Force refresh from GitHub

Response:
```json
{
  "success": true,
  "count": 10,
  "repositories": [
    {
      "id": 123,
      "name": "my-app",
      "full_name": "username/my-app",
      "description": "My awesome app",
      "language": "Python",
      "clone_url": "https://github.com/username/my-app.git",
      "default_branch": "main",
      "private": false
    }
  ]
}
```

---

### POST /github/import
**Import project from GitHub**

Headers:
- `X-User-ID: user123`

Body:
```json
{
  "owner": "username",
  "repo": "my-app",
  "branch": "main"
}
```

Response:
```json
{
  "success": true,
  "project": {
    "full_name": "username/my-app",
    "branch": "main",
    "local_path": "/workspace/user123/username-my-app",
    "language": "python",
    "framework": "fastapi",
    "status": "ready"
  },
  "message": "Project imported and ready to build"
}
```

---

### GET /github/projects
**Get imported projects**

Headers:
- `X-User-ID: user123`

Response:
```json
{
  "success": true,
  "count": 3,
  "projects": [
    {
      "full_name": "username/my-app",
      "branch": "main",
      "local_path": "/workspace/user123/username-my-app",
      "language": "python",
      "framework": "fastapi",
      "imported_at": "2024-02-18T12:00:00",
      "status": "ready"
    }
  ]
}
```

---

### POST /github/sync
**Sync project with latest changes**

Headers:
- `X-User-ID: user123`

Body:
```json
{
  "owner": "username",
  "repo": "my-app"
}
```

Response:
```json
{
  "success": true,
  "message": "Project synced with latest changes"
}
```

---

### DELETE /github/projects/{owner}/{repo}
**Delete imported project**

Headers:
- `X-User-ID: user123`

Response:
```json
{
  "success": true,
  "message": "Project username/my-app deleted"
}
```

---

## 🔐 GitHub Token

### Get Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` - Full control of repositories
   - `user` - Read user profile
4. Generate token
5. Save token (e.g., `ghp_xxxxxxxxxxxxx`)

### Use Token

```bash
export GITHUB_TOKEN="ghp_your_token_here"

curl -X POST http://localhost:8007/github/connect \
  -H "X-User-ID: user123" \
  -d "{\"access_token\": \"$GITHUB_TOKEN\"}"
```

---

## 💾 MongoDB Storage

### Collections Used

**users** - GitHub account connections
```json
{
  "user_id": "user123",
  "github": {
    "connected": true,
    "username": "github_username",
    "access_token": "ghp_token",
    "connected_at": "2024-02-18T12:00:00"
  }
}
```

**projects** - Imported projects
```json
{
  "user_id": "user123",
  "source": "github",
  "full_name": "username/my-app",
  "branch": "main",
  "local_path": "/workspace/user123/username-my-app",
  "language": "python",
  "framework": "fastapi",
  "imported": true,
  "imported_at": "2024-02-18T12:00:00",
  "status": "ready"
}
```

---

## 🔄 Integration with Build Agent

### Workflow

1. **Connect GitHub** → User connects account
2. **Browse Repos** → User selects project
3. **Import Project** → Clone to workspace
4. **Build** → Pass `local_path` to Build Agent
5. **Deploy** → Deploy built container

### Example Flow

```bash
# 1. Import project
IMPORT=$(curl -X POST http://localhost:8007/github/import \
  -H "X-User-ID: user123" \
  -d '{"owner": "user", "repo": "app"}')

LOCAL_PATH=$(echo $IMPORT | jq -r '.project.local_path')

# 2. Build with Build Agent
curl -X POST http://localhost:8001/build \
  -d "{
    \"project_path\": \"$LOCAL_PATH\",
    \"image_name\": \"my-app\",
    \"tag\": \"latest\"
  }"
```

---

## 🌐 API Gateway Integration

### Add to Gateway Routes

```python
# In api-gateway/gateway.py
AGENTS = {
    "github": {
        "name": "GitHub Agent",
        "url": "http://github-agent:8007",
        "status": "active",
        "enabled": True
    }
}

@app.api_route("/github/{path:path}", methods=["GET", "POST", "DELETE"])
async def proxy_github(request: Request, path: str):
    return await proxy_request("github", path, request)
```

### Via Gateway

```bash
# Through API Gateway
curl -X POST http://localhost:8000/github/import \
  -H "X-User-ID: user123" \
  -d '{"owner": "user", "repo": "app"}'
```

---

## 📁 Workspace Structure

```
/workspace/
├── user123/
│   ├── username-my-app/
│   │   ├── src/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── username-another-app/
│       └── ...
└── user456/
    └── ...
```

---

## 🧪 Testing

```bash
# Test connection
curl http://localhost:8007/health

# Test with real GitHub account
export GITHUB_TOKEN="ghp_your_token"
export USER_ID="testuser"

# Connect
curl -X POST http://localhost:8007/github/connect \
  -H "X-User-ID: $USER_ID" \
  -d "{\"access_token\": \"$GITHUB_TOKEN\"}"

# List repos
curl http://localhost:8007/github/repos \
  -H "X-User-ID: $USER_ID"

# Import first repo
curl -X POST http://localhost:8007/github/import \
  -H "X-User-ID: $USER_ID" \
  -d '{"owner": "your-username", "repo": "your-repo"}'
```

---

## 🐛 Troubleshooting

### GitHub API Rate Limits
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour
- Check: https://api.github.com/rate_limit

### Clone Failures
- Check GitHub token has `repo` scope
- Verify repository exists and is accessible
- Check workspace directory permissions

### Import Errors
- Ensure MongoDB is running
- Check GitHub account is connected
- Verify repository name is correct

---

## ✅ Features Summary

- ✅ GitHub OAuth integration
- ✅ Repository browsing
- ✅ Project cloning
- ✅ Language detection
- ✅ Project sync
- ✅ MongoDB persistence
- ✅ REST API
- ✅ Docker ready

---

**Ready to import projects from GitHub!** 🔗✨
