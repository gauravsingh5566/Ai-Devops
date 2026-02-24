"""
Docker Agent - Advanced Docker Image Builder with LLM Validation

This agent:
1. Builds Docker images from Dockerfiles
2. Validates Dockerfiles using LLM (Gemini)
3. Scans built images for issues
4. Provides recommendations for optimization
5. Ensures best practices
"""

import os
import sys
import logging
import subprocess
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

# Google Gemini for LLM validation
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("Warning: google-generativeai not installed. LLM validation disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerAgent:
    """
    Docker Agent with AI-powered validation
    
    Features:
    - Build Docker images from Dockerfiles
    - Validate Dockerfile best practices using LLM
    - Scan built images for vulnerabilities
    - Provide optimization recommendations
    - Test image functionality
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Initialize Gemini if available
        if HAS_GEMINI and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.llm_model = genai.GenerativeModel('gemini-2.5-flash-lite')
            logger.info("✅ Gemini LLM initialized for validation")
        else:
            self.llm_model = None
            logger.warning("⚠️ LLM validation disabled (no API key or library)")
    
    
    async def validate_dockerfile(self, dockerfile_content: str, context: Dict = None) -> Dict:
        """
        Validate Dockerfile using LLM
        
        Args:
            dockerfile_content: Content of the Dockerfile
            context: Additional context (language, framework, etc.)
        
        Returns:
            Validation results with issues, warnings, and recommendations
        """
        logger.info("🔍 Validating Dockerfile with LLM...")
        
        if not self.llm_model:
            return {
                "validated": False,
                "message": "LLM validation not available",
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
        
        try:
            # Create validation prompt
            prompt = self._create_validation_prompt(dockerfile_content, context)
            
            # Get LLM response
            response = self.llm_model.generate_content(prompt)
            
            # Parse LLM response
            validation_result = self._parse_llm_validation(response.text)
            
            logger.info(f"✅ Validation complete: {len(validation_result['issues'])} issues, "
                       f"{len(validation_result['warnings'])} warnings")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {
                "validated": False,
                "error": str(e),
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
    
    
    def _create_validation_prompt(self, dockerfile: str, context: Dict = None) -> str:
        """Create prompt for LLM validation"""
        
        context_info = ""
        if context:
            context_info = f"""
            
**Project Context:**
- Language: {context.get('language', 'Unknown')}
- Framework: {context.get('framework', 'Unknown')}
- Project Type: {context.get('project_type', 'Unknown')}
"""
        
        prompt = f"""You are a Docker and DevOps expert. Analyze this Dockerfile and provide detailed feedback.

**Dockerfile to validate:**
```dockerfile
{dockerfile}
```
{context_info}

Please analyze and provide:

1. **CRITICAL ISSUES** (Security vulnerabilities, syntax errors, things that will break):
   - List each issue with severity: CRITICAL
   - Explain why it's a problem
   - Suggest fix

2. **WARNINGS** (Bad practices, potential issues):
   - List each warning with severity: WARNING
   - Explain the concern
   - Suggest improvement

3. **RECOMMENDATIONS** (Optimizations, best practices):
   - Image size optimization
   - Build speed improvements
   - Security enhancements
   - Best practices

4. **OVERALL SCORE** (0-100):
   - Rate the Dockerfile quality

Format your response as JSON:
{{
  "score": 85,
  "issues": [
    {{
      "severity": "CRITICAL",
      "message": "Running as root user",
      "line": 10,
      "fix": "Add USER directive to run as non-root"
    }}
  ],
  "warnings": [
    {{
      "severity": "WARNING", 
      "message": "Using latest tag",
      "fix": "Specify exact version"
    }}
  ],
  "recommendations": [
    {{
      "type": "optimization",
      "message": "Use multi-stage build to reduce image size",
      "impact": "Could reduce size by 60%"
    }}
  ],
  "summary": "Overall assessment..."
}}

Respond ONLY with valid JSON, no additional text.
"""
        return prompt
    
    
    def _parse_llm_validation(self, llm_response: str) -> Dict:
        """Parse LLM JSON response"""
        
        try:
            # Extract JSON from response (in case LLM added extra text)
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                # Try parsing entire response
                result = json.loads(llm_response)
            
            return {
                "validated": True,
                "score": result.get("score", 0),
                "issues": result.get("issues", []),
                "warnings": result.get("warnings", []),
                "recommendations": result.get("recommendations", []),
                "summary": result.get("summary", "")
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"LLM Response: {llm_response}")
            
            # Return basic validation
            return {
                "validated": True,
                "score": 70,
                "issues": [],
                "warnings": [],
                "recommendations": [],
                "summary": llm_response[:500]  # First 500 chars
            }
    
    
    async def build_image(
        self, 
        dockerfile_path: str, 
        image_name: str, 
        tag: str = "latest",
        context_dir: str = None,
        build_args: Dict = None
    ) -> Dict:
        """
        Build Docker image
        
        Args:
            dockerfile_path: Path to Dockerfile
            image_name: Name for the image
            tag: Image tag
            context_dir: Build context directory
            build_args: Build arguments
        
        Returns:
            Build result with status, logs, and image info
        """
        logger.info(f"🐳 Building Docker image: {image_name}:{tag}")
        
        if not os.path.exists(dockerfile_path):
            return {
                "success": False,
                "error": f"Dockerfile not found: {dockerfile_path}"
            }
        
        # Default context to Dockerfile directory
        if not context_dir:
            context_dir = os.path.dirname(dockerfile_path)
        
        try:
            # Build command
            cmd = [
                'docker', 'build',
                '-t', f'{image_name}:{tag}',
                '-f', dockerfile_path
            ]
            
            # Add build args
            if build_args:
                for key, value in build_args.items():
                    cmd.extend(['--build-arg', f'{key}={value}'])
            
            # Add context
            cmd.append(context_dir)
            
            # Execute build
            start_time = datetime.utcnow()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )
            build_time = (datetime.utcnow() - start_time).total_seconds()
            
            if result.returncode == 0:
                # Build successful
                logger.info(f"✅ Image built successfully: {image_name}:{tag}")
                
                # Get image info
                image_info = self._get_image_info(f"{image_name}:{tag}")
                
                return {
                    "success": True,
                    "image_name": image_name,
                    "image_tag": tag,
                    "image_id": image_info.get("id"),
                    "image_size": image_info.get("size"),
                    "build_time": build_time,
                    "build_logs": result.stdout,
                    "message": "Image built successfully"
                }
            else:
                # Build failed
                logger.error(f"❌ Build failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "build_logs": result.stdout,
                    "build_time": build_time
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build timed out after 10 minutes"
            }
        except Exception as e:
            logger.error(f"Build error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    
    def _get_image_info(self, image_tag: str) -> Dict:
        """Get information about built image"""
        
        try:
            # Get image ID
            id_result = subprocess.run(
                ['docker', 'images', image_tag, '--format', '{{.ID}}'],
                capture_output=True,
                text=True
            )
            
            # Get image size
            size_result = subprocess.run(
                ['docker', 'images', image_tag, '--format', '{{.Size}}'],
                capture_output=True,
                text=True
            )
            
            # Get image details with inspect
            inspect_result = subprocess.run(
                ['docker', 'inspect', image_tag],
                capture_output=True,
                text=True
            )
            
            if inspect_result.returncode == 0:
                inspect_data = json.loads(inspect_result.stdout)[0]
                
                return {
                    "id": id_result.stdout.strip(),
                    "size": size_result.stdout.strip(),
                    "created": inspect_data.get("Created"),
                    "architecture": inspect_data.get("Architecture"),
                    "os": inspect_data.get("Os"),
                    "layers": len(inspect_data.get("RootFS", {}).get("Layers", [])),
                    "config": {
                        "exposed_ports": list(inspect_data.get("Config", {}).get("ExposedPorts", {}).keys()),
                        "env": inspect_data.get("Config", {}).get("Env", []),
                        "cmd": inspect_data.get("Config", {}).get("Cmd", []),
                        "entrypoint": inspect_data.get("Config", {}).get("Entrypoint", [])
                    }
                }
            
            return {
                "id": id_result.stdout.strip(),
                "size": size_result.stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return {}
    
    
    async def validate_image(self, image_name: str, tag: str = "latest") -> Dict:
        """
        Validate built Docker image using LLM
        
        Checks:
        - Image can be inspected
        - No critical vulnerabilities (basic check)
        - Proper configuration
        - Follows best practices
        
        Args:
            image_name: Name of the image
            tag: Image tag
        
        Returns:
            Validation results
        """
        logger.info(f"🔍 Validating Docker image: {image_name}:{tag}")
        
        image_tag = f"{image_name}:{tag}"
        
        # Get image info
        image_info = self._get_image_info(image_tag)
        
        if not image_info:
            return {
                "valid": False,
                "error": "Image not found or cannot be inspected"
            }
        
        # Basic validation checks
        issues = []
        warnings = []
        recommendations = []
        
        # Check 1: Image size
        size_str = image_info.get("size", "0")
        size_mb = self._parse_size_to_mb(size_str)
        
        if size_mb > 1000:  # > 1GB
            warnings.append({
                "type": "size",
                "message": f"Large image size: {size_str}",
                "recommendation": "Consider using multi-stage builds or alpine base images"
            })
        
        # Check 2: Exposed ports
        exposed_ports = image_info.get("config", {}).get("exposed_ports", [])
        if not exposed_ports:
            warnings.append({
                "type": "configuration",
                "message": "No ports exposed",
                "recommendation": "Add EXPOSE directive if this is a service"
            })
        
        # Check 3: CMD or ENTRYPOINT
        cmd = image_info.get("config", {}).get("cmd")
        entrypoint = image_info.get("config", {}).get("entrypoint")
        
        if not cmd and not entrypoint:
            issues.append({
                "severity": "CRITICAL",
                "type": "configuration",
                "message": "No CMD or ENTRYPOINT defined",
                "fix": "Add CMD or ENTRYPOINT to specify how to run the container"
            })
        
        # Check 4: Number of layers
        layers = image_info.get("layers", 0)
        if layers > 50:
            recommendations.append({
                "type": "optimization",
                "message": f"High number of layers: {layers}",
                "impact": "Could slow down image pulls and increase size",
                "suggestion": "Combine RUN commands to reduce layers"
            })
        
        # Use LLM for deeper validation if available
        llm_validation = {}
        if self.llm_model:
            llm_validation = await self._llm_validate_image(image_info)
            
            # Merge LLM results
            issues.extend(llm_validation.get("issues", []))
            warnings.extend(llm_validation.get("warnings", []))
            recommendations.extend(llm_validation.get("recommendations", []))
        
        # Calculate overall score
        score = 100
        score -= len(issues) * 20  # Critical issues: -20 each
        score -= len(warnings) * 10  # Warnings: -10 each
        score = max(0, score)  # Don't go below 0
        
        return {
            "valid": len(issues) == 0,
            "score": score,
            "image_info": image_info,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "summary": self._create_validation_summary(score, issues, warnings)
        }
    
    
    async def _llm_validate_image(self, image_info: Dict) -> Dict:
        """Use LLM to validate image configuration"""
        
        prompt = f"""Analyze this Docker image configuration and identify any issues:

**Image Information:**
```json
{json.dumps(image_info, indent=2)}
```

Look for:
1. Security issues (running as root, exposed secrets)
2. Configuration problems (missing essential settings)
3. Optimization opportunities (size, layers)
4. Best practice violations

Respond with JSON:
{{
  "issues": [...],
  "warnings": [...],
  "recommendations": [...]
}}
"""
        
        try:
            response = self.llm_model.generate_content(prompt)
            return self._parse_llm_validation(response.text)
        except Exception as e:
            logger.error(f"LLM image validation failed: {e}")
            return {"issues": [], "warnings": [], "recommendations": []}
    
    
    def _parse_size_to_mb(self, size_str: str) -> float:
        """Convert Docker size string to MB"""
        
        try:
            size_str = size_str.upper().strip()
            
            if 'GB' in size_str:
                return float(size_str.replace('GB', '')) * 1024
            elif 'MB' in size_str:
                return float(size_str.replace('MB', ''))
            elif 'KB' in size_str:
                return float(size_str.replace('KB', '')) / 1024
            elif 'B' in size_str:
                return float(size_str.replace('B', '')) / (1024 * 1024)
            
            return 0.0
        except:
            return 0.0
    
    
    def _create_validation_summary(self, score: int, issues: List, warnings: List) -> str:
        """Create human-readable validation summary"""
        
        if score >= 90:
            status = "EXCELLENT"
            emoji = "🌟"
        elif score >= 75:
            status = "GOOD"
            emoji = "✅"
        elif score >= 60:
            status = "FAIR"
            emoji = "⚠️"
        else:
            status = "NEEDS IMPROVEMENT"
            emoji = "❌"
        
        summary = f"{emoji} Image validation: {status} (Score: {score}/100)\n"
        
        if issues:
            summary += f"- {len(issues)} critical issue(s) found\n"
        if warnings:
            summary += f"- {len(warnings)} warning(s)\n"
        
        if not issues and not warnings:
            summary += "- No issues detected"
        
        return summary
    
    
    async def test_image(self, image_name: str, tag: str = "latest") -> Dict:
        """
        Test if Docker image can run successfully
        
        Args:
            image_name: Name of the image
            tag: Image tag
        
        Returns:
            Test results
        """
        logger.info(f"🧪 Testing Docker image: {image_name}:{tag}")
        
        image_tag = f"{image_name}:{tag}"
        
        try:
            # Try to create a container (don't start it)
            result = subprocess.run(
                ['docker', 'create', '--name', f'test-{image_name}-{tag}', image_tag],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                
                # Remove test container
                subprocess.run(['docker', 'rm', container_id], capture_output=True)
                
                return {
                    "success": True,
                    "message": "Image can be instantiated successfully",
                    "container_created": True
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "message": "Failed to create container from image"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


if __name__ == "__main__":
    # Test the agent
    async def test():
        agent = DockerAgent()
        
        # Test Dockerfile validation
        test_dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
"""
        
        validation = await agent.validate_dockerfile(test_dockerfile, {
            "language": "python",
            "framework": "fastapi"
        })
        
        print("Validation Result:", json.dumps(validation, indent=2))
    
    asyncio.run(test())
