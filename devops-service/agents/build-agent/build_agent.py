"""
Build Agent - AI-Powered Docker Container Builder
"""
import os
import json
import logging
import subprocess
from typing import Dict, Optional, Tuple

from llm_detector import get_detector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuildAgent:
    def __init__(self):
        self.supported_languages = ['python', 'node', 'java', 'go', 'rust', 'ruby']
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.detector = get_detector(self.gemini_api_key)
        logger.info("✅ Build Agent initialized with LLM-powered detection")
    
    async def analyze_project(self, project_path: str) -> Dict:
        """
        Analyze project using AI-powered detection
        
        Uses LLM (Gemini) to intelligently detect language, framework,
        and project details. Falls back to file-based detection if needed.
        """
        logger.info(f"🔍 Analyzing project at: {project_path}")
        
        if not os.path.exists(project_path):
            logger.error(f"Project path not found: {project_path}")
            return {
                'language': None,
                'framework': None,
                'error': 'Project path not found'
            }
        
        try:
            # Use LLM-powered detection
            result = await self.detector.detect(project_path, min_confidence=70)
            
            logger.info(f"✅ Detection complete:")
            logger.info(f"   Language: {result.get('language')}")
            logger.info(f"   Framework: {result.get('framework')}")
            logger.info(f"   Method: {result.get('detected_by')}")
            logger.info(f"   Confidence: {result.get('confidence')}%")
            
            # Build project_info dict
            project_info = {
                'language': result.get('language'),
                'framework': result.get('framework'),
                'project_type': result.get('project_type', 'application'),
                'confidence': result.get('confidence', 0),
                'detected_by': result.get('detected_by', 'unknown'),
                'package_manager': self._infer_package_manager(result.get('language')),
                'entry_point': self._find_entry_point(project_path, result.get('language')),
                'suggested_port': result.get('suggested_port', 8000),
                'base_image': result.get('base_image'),
            }
            
            # Add AI reasoning if available
            if 'reasoning' in result:
                project_info['ai_reasoning'] = result['reasoning']
                logger.info(f"   Reasoning: {result['reasoning'][:100]}...")
            
            return project_info
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Return minimal info
            return {
                'language': None,
                'framework': None,
                'confidence': 0,
                'error': str(e),
                'detected_by': 'failed'
            }
    
    def _infer_package_manager(self, language: str) -> Optional[str]:
        """Infer package manager from language"""
        managers = {
            'python': 'pip',
            'node': 'npm',
            'java': 'maven',
            'go': 'go',
            'rust': 'cargo',
            'ruby': 'bundler',
            'php': 'composer',
        }
        return managers.get(language)
    
    def _find_entry_point(self, project_path: str, language: str) -> Optional[str]:
        """Find likely entry point file"""
        if not language:
            return None
        
        files = os.listdir(project_path) if os.path.exists(project_path) else []
        
        entry_points = {
            'python': ['main.py', 'app.py', 'manage.py', '__main__.py', 'wsgi.py'],
            'node': ['index.js', 'server.js', 'app.js', 'main.js'],
            'java': ['Main.java', 'Application.java'],
            'go': ['main.go'],
            'rust': ['main.rs'],
            'ruby': ['app.rb', 'main.rb'],
        }
        
        for entry in entry_points.get(language, []):
            if entry in files:
                return entry
        
        return None
    
    def generate_dockerfile(self, project_info: Dict) -> str:
        """
        Generate Dockerfile using LLM for intelligent, customized generation
        Falls back to template-based generation if LLM fails
        """
        try:
            # Try LLM-powered generation first
            if self.gemini_api_key and self.detector.model:
                logger.info("🤖 Generating Dockerfile with AI...")
                dockerfile = self._generate_dockerfile_with_llm(project_info)
                if dockerfile:
                    logger.info("✅ AI-generated Dockerfile created")
                    return dockerfile
                else:
                    logger.warning("AI generation returned empty, using template")
            else:
                logger.info("No LLM available, using template-based generation")
        except Exception as e:
            logger.error(f"LLM Dockerfile generation failed: {e}, using template")
        
        # Fallback to template-based generation
        return self._generate_dockerfile_template(project_info)
    
    def _generate_dockerfile_with_llm(self, project_info: Dict) -> Optional[str]:
        """
        Use Gemini LLM to generate optimized, production-ready Dockerfile
        """
        lang = project_info.get('language', 'unknown')
        framework = project_info.get('framework', 'none')
        project_type = project_info.get('project_type', 'application')
        entry_point = project_info.get('entry_point', 'main')
        port = project_info.get('suggested_port', 8000)
        base_image = project_info.get('base_image', '')
        reasoning = project_info.get('ai_reasoning', '')
        
        # Create comprehensive prompt with project context
        prompt = f"""You are a Docker and DevOps expert. Generate a production-ready, optimized Dockerfile for this project:

**Project Details:**
- Language: {lang}
- Framework: {framework}
- Project Type: {project_type}
- Entry Point: {entry_point}
- Suggested Port: {port}
- Recommended Base Image: {base_image}

**AI Analysis:**
{reasoning}

**Requirements:**
1. Use multi-stage builds when beneficial (especially for frontend apps like Angular, React, Vue)
2. Optimize for small image size (use alpine, slim variants)
3. Use specific version tags (not :latest)
4. Include proper WORKDIR
5. Copy dependencies file first (for Docker layer caching)
6. Use --no-cache-dir for pip, npm ci for npm (faster, deterministic)
7. Run as non-root user when possible (security best practice)
8. Expose the correct port
9. Use production-optimized build commands
10. For Angular/React/Vue: Use nginx:alpine for serving static files in production
11. Include HEALTHCHECK when applicable
12. Add LABEL metadata (maintainer, description, version)

**Specific Framework Guidelines:**
- **Angular**: Multi-stage build → Stage 1: node:18-alpine build, Stage 2: nginx:alpine serve dist
- **React/Vue**: Multi-stage build → Stage 1: node:18-alpine build, Stage 2: nginx:alpine serve build
- **Next.js**: Use standalone output mode, single stage with node:18-alpine
- **Python (Flask/Django/FastAPI)**: Use python:3.11-slim, install deps, expose port
- **Node.js (Express)**: Use node:18-alpine, install deps, expose port
- **Java (Spring)**: Multi-stage → Stage 1: maven/gradle build, Stage 2: openjdk:17-jre-slim run

**Output Format:**
Respond with ONLY the Dockerfile content. No explanations, no markdown code blocks, no preamble. Start with FROM and end with CMD/ENTRYPOINT.

Generate the Dockerfile:"""

        try:
            # Call Gemini
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            logger.info("📤 Sending Dockerfile generation request to Gemini...")
            response = model.generate_content(prompt)
            dockerfile = response.text.strip()
            
            # Clean up response (remove markdown if present)
            if dockerfile.startswith('```dockerfile'):
                dockerfile = dockerfile[13:]
            elif dockerfile.startswith('```'):
                dockerfile = dockerfile[3:]
            if dockerfile.endswith('```'):
                dockerfile = dockerfile[:-3]
            
            dockerfile = dockerfile.strip()
            
            # Validate it looks like a Dockerfile
            if not dockerfile.startswith('FROM'):
                logger.warning("⚠️ Generated content doesn't start with FROM, might not be valid")
                return None
            
            if len(dockerfile) < 50:
                logger.warning("⚠️ Generated Dockerfile too short, might be invalid")
                return None
            
            logger.info(f"✅ AI-generated Dockerfile: {len(dockerfile)} chars, {dockerfile.count('FROM')} stages")
            return dockerfile
            
        except Exception as e:
            logger.error(f"❌ LLM Dockerfile generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_dockerfile_template(self, project_info: Dict) -> str:
        """
        Template-based Dockerfile generation (fallback)
        """
        logger.info("Using template-based Dockerfile generation")
        lang = project_info.get('language', '').lower()
        framework = project_info.get('framework', '').lower()
        
        # Normalize TypeScript/JavaScript
        if lang in ['typescript', 'javascript']:
            lang = 'node'
        
        if lang == 'python':
            return self._python_dockerfile(project_info)
        elif lang == 'node':
            # Check framework for specific handling
            if framework in ['angular', 'react', 'vue', 'next', 'nuxt']:
                return self._frontend_dockerfile(project_info)
            else:
                return self._node_dockerfile(project_info)
        elif lang == 'java':
            return self._java_dockerfile(project_info)
        elif lang == 'go':
            return self._go_dockerfile(project_info)
        else:
            logger.warning(f"Unsupported language: {lang}, using generic Node.js Dockerfile")
            return self._node_dockerfile(project_info)
    
    def _python_dockerfile(self, info: Dict) -> str:
        entry = info.get('entry_point', 'main.py')
        return f"""FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "{entry}"]
"""
    
    def _node_dockerfile(self, info: Dict) -> str:
        entry = info.get('entry_point', 'index.js')
        port = info.get('suggested_port', 3000)
        return f"""FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE {port}
CMD ["node", "{entry}"]
"""
    
    def _frontend_dockerfile(self, info: Dict) -> str:
        """Generate Dockerfile for frontend frameworks (Angular, React, Vue, etc.)"""
        framework = info.get('framework', '').lower()
        port = info.get('suggested_port', 4200)
        
        if framework == 'angular':
            return f"""# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build --prod

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist/* /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        elif framework in ['react', 'vue']:
            return f"""# Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage  
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        elif framework == 'next':
            return f"""FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
"""
        else:
            # Generic frontend build
            return f"""FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE {port}
CMD ["npm", "start"]
"""
    
    def _java_dockerfile(self, info: Dict) -> str:
        return """FROM maven:3.8-openjdk-17 as build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests
FROM openjdk:17-jre-slim
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
"""
    
    def _go_dockerfile(self, info: Dict) -> str:
        return """FROM golang:1.21-alpine as build
WORKDIR /app
COPY . .
RUN go build -o main .
FROM alpine:latest
COPY --from=build /app/main .
EXPOSE 8080
CMD ["./main"]
"""
    
    async def save_dockerfile(self, project_path: str, dockerfile_content: str, 
                             project_info: Dict = None) -> Tuple[bool, str]:
        """
        Save generated Dockerfile to project directory
        Also creates supporting files (nginx.conf for Angular, etc.)
        """
        logger.info(f"💾 Saving Dockerfile to {project_path}")
        
        try:
            # Write Dockerfile
            dockerfile_path = os.path.join(project_path, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            logger.info(f"✅ Dockerfile saved ({len(dockerfile_content)} chars)")
            
            # If it's an Angular/React/Vue project, create nginx.conf
            if project_info:
                framework = project_info.get('framework', '').lower()
                if framework in ['angular', 'react', 'vue']:
                    nginx_conf = """server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
                    nginx_path = os.path.join(project_path, 'nginx.conf')
                    with open(nginx_path, 'w') as f:
                        f.write(nginx_conf)
                    logger.info(f"✅ Created nginx.conf for {framework} project")
            
            return True, f"Dockerfile saved to {dockerfile_path}"
            
        except Exception as e:
            logger.error(f"❌ Failed to save Dockerfile: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)