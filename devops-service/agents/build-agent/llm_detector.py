"""
LLM-Powered Language and Framework Detection
Uses Google Gemini AI to intelligently analyze projects
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("Warning: google-generativeai not installed. LLM detection disabled.")

logger = logging.getLogger(__name__)

# Important configuration files to read completely
IMPORTANT_FILES = [
    'requirements.txt',
    'package.json',
    'package-lock.json',
    'pom.xml',
    'build.gradle',
    'go.mod',
    'go.sum',
    'Cargo.toml',
    'composer.json',
    'Gemfile',
    'Gemfile.lock',
    '.env.example',
    'README.md',
    'Dockerfile',
    'docker-compose.yml',
    'setup.py',
    'pyproject.toml',
    'Pipfile',
    'yarn.lock',
    'pnpm-lock.yaml',
]

# Code file extensions to sample
CODE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cs': 'csharp',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
}

# Ignore directories
IGNORE_DIRS = {
    'node_modules',
    '__pycache__',
    '.git',
    '.venv',
    'venv',
    'env',
    'dist',
    'build',
    'target',
    '.idea',
    '.vscode',
}


class LLMDetector:
    """
    AI-powered project detection using Gemini LLM
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model = None
        
        if HAS_GEMINI and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
                logger.info("✅ Gemini LLM initialized for detection")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            logger.warning("⚠️ LLM detection unavailable (no API key or library)")
    
    
    def scan_project_enhanced(self, project_path: str, max_files: int = 50) -> Dict:
        """
        Enhanced project scanning with file content sampling
        
        Args:
            project_path: Path to the project directory
            max_files: Maximum number of files to scan
            
        Returns:
            Dictionary with project structure and samples
        """
        logger.info(f"Scanning project: {project_path}")
        
        project_data = {
            'files': [],
            'directories': [],
            'config_files': {},
            'code_samples': {},
            'file_counts': {},
            'total_files': 0,
        }
        
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Remove ignored directories
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                
                # Get relative directory path
                rel_dir = os.path.relpath(root, project_path)
                if rel_dir != '.':
                    project_data['directories'].append(rel_dir)
                
                for file in files:
                    if file_count >= max_files:
                        break
                    
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, project_path)
                    
                    # Add to files list
                    project_data['files'].append(relative_path)
                    project_data['total_files'] += 1
                    file_count += 1
                    
                    # Count file types
                    extension = os.path.splitext(file)[1]
                    if extension:
                        project_data['file_counts'][extension] = \
                            project_data['file_counts'].get(extension, 0) + 1
                    
                    # Read important configuration files
                    if file in IMPORTANT_FILES:
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                # Limit size
                                if len(content) > 10000:
                                    content = content[:10000] + "\n... (truncated)"
                                project_data['config_files'][file] = content
                                logger.debug(f"Read config file: {file}")
                        except Exception as e:
                            logger.warning(f"Could not read {file}: {e}")
                    
                    # Sample code files
                    extension = os.path.splitext(file)[1]
                    if extension in CODE_EXTENSIONS:
                        if extension not in project_data['code_samples']:
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = f.readlines()[:100]  # First 100 lines
                                    sample = ''.join(lines)
                                    if len(sample) > 2000:
                                        sample = sample[:2000] + "\n... (truncated)"
                                    project_data['code_samples'][extension] = sample
                                    logger.debug(f"Sampled {extension} file")
                            except Exception as e:
                                logger.warning(f"Could not sample {filepath}: {e}")
        
        except Exception as e:
            logger.error(f"Error scanning project: {e}")
        
        logger.info(f"Scanned {project_data['total_files']} files, "
                   f"{len(project_data['config_files'])} config files, "
                   f"{len(project_data['code_samples'])} code samples")
        
        return project_data
    
    
    def create_detection_prompt(self, project_data: Dict) -> str:
        """
        Create a detailed prompt for LLM analysis
        """
        
        prompt = """You are an expert software engineer and DevOps specialist. Analyze this project and determine:

1. Primary programming language
2. Framework/library being used
3. Project type (web_api, web_app, cli, library, microservice, etc.)
4. Recommended base Docker image
5. Suggested port for the application
6. Confidence level (0-100)

**Project Structure:**
"""
        
        # Add file statistics
        prompt += f"Total files: {project_data['total_files']}\n"
        prompt += f"Directories: {len(project_data['directories'])}\n"
        
        # Add file type counts
        if project_data['file_counts']:
            prompt += "\nFile types found:\n"
            sorted_types = sorted(project_data['file_counts'].items(), 
                                key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:10]:
                prompt += f"  {ext}: {count} files\n"
        
        # Add important files found
        if project_data['config_files']:
            prompt += f"\nConfiguration files found: {', '.join(project_data['config_files'].keys())}\n"
        
        # Add configuration file contents
        if project_data['config_files']:
            prompt += "\n**Configuration Files Content:**\n"
            for filename, content in project_data['config_files'].items():
                prompt += f"\n--- {filename} ---\n"
                # Limit content length
                if len(content) > 1500:
                    prompt += content[:1500] + "\n... (content truncated for brevity)\n"
                else:
                    prompt += content + "\n"
        
        # Add code samples
        if project_data['code_samples']:
            prompt += "\n**Code Samples:**\n"
            for extension, sample in project_data['code_samples'].items():
                lang = CODE_EXTENSIONS.get(extension, extension)
                prompt += f"\n--- Sample {lang} file ({extension}) ---\n"
                # Limit sample length
                if len(sample) > 1000:
                    prompt += sample[:1000] + "\n... (sample truncated)\n"
                else:
                    prompt += sample + "\n"
        
        # Add directory structure sample
        if project_data['directories']:
            prompt += f"\n**Directory Structure (sample):**\n"
            for dir_path in project_data['directories'][:20]:
                prompt += f"  {dir_path}/\n"
        
        # Request structured response
        prompt += """

**IMPORTANT: Respond in valid JSON format ONLY. No other text.**

Example response format:
{
  "language": "python",
  "framework": "fastapi",
  "project_type": "web_api",
  "version": "3.11",
  "confidence": 95,
  "reasoning": "Project uses FastAPI framework as indicated by requirements.txt dependencies and FastAPI decorators in code samples",
  "base_image": "python:3.11-slim",
  "suggested_port": 8000,
  "additional_info": {
    "package_manager": "pip",
    "has_tests": true,
    "async_support": true
  }
}

Provide your analysis as JSON:
"""
        
        return prompt
    
    
    def parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse and validate LLM JSON response
        """
        try:
            # Clean response
            cleaned = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]
            
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Parse JSON
            result = json.loads(cleaned)
            
            # Validate required fields
            required_fields = ['language', 'confidence']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure confidence is a number
            result['confidence'] = int(result.get('confidence', 0))
            
            # Add defaults for optional fields
            if 'framework' not in result:
                result['framework'] = None
            if 'project_type' not in result:
                result['project_type'] = 'application'
            if 'suggested_port' not in result:
                result['suggested_port'] = 8000
            
            logger.info(f"✅ LLM detected: {result['language']}/{result['framework']} "
                       f"(confidence: {result['confidence']}%)")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response_text[:500]}")
            raise
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            raise
    
    
    async def detect_with_llm(self, project_path: str) -> Dict:
        """
        Use LLM to detect language and framework
        
        Returns:
            Detection result with language, framework, confidence, etc.
        """
        
        if not self.model:
            raise Exception("LLM model not available")
        
        try:
            # 1. Scan project
            logger.info("📊 Scanning project structure...")
            project_data = self.scan_project_enhanced(project_path)
            
            # 2. Create prompt
            logger.info("🤖 Creating LLM analysis prompt...")
            prompt = self.create_detection_prompt(project_data)
            
            # 3. Call LLM
            logger.info("🔍 Calling Gemini AI for analysis...")
            response = self.model.generate_content(prompt)
            
            # 4. Parse response
            logger.info("📋 Parsing LLM response...")
            result = self.parse_llm_response(response.text)
            
            # 5. Add metadata
            result['detected_by'] = 'llm'
            result['fallback_used'] = False
            result['success'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"LLM detection failed: {e}")
            raise
    
    
    def fallback_detection(self, project_path: str) -> Dict:
        """
        Fallback to simple file-based detection
        """
        logger.info("Using fallback file-based detection...")
        
        project_data = self.scan_project_enhanced(project_path)
        config_files = project_data['config_files']
        
        result = {
            'language': None,
            'framework': None,
            'project_type': 'application',
            'confidence': 60,
            'detected_by': 'fallback',
            'fallback_used': True,
            'success': True,
            'suggested_port': 8000,
        }
        
        # Python detection
        if 'requirements.txt' in config_files or 'setup.py' in config_files or 'pyproject.toml' in config_files:
            result['language'] = 'python'
            result['base_image'] = 'python:3.11-slim'
            
            # Detect framework
            content = config_files.get('requirements.txt', '') + \
                     config_files.get('setup.py', '') + \
                     config_files.get('pyproject.toml', '')
            content_lower = content.lower()
            
            if 'fastapi' in content_lower:
                result['framework'] = 'fastapi'
                result['project_type'] = 'web_api'
                result['suggested_port'] = 8000
            elif 'django' in content_lower:
                result['framework'] = 'django'
                result['project_type'] = 'web_app'
                result['suggested_port'] = 8000
            elif 'flask' in content_lower:
                result['framework'] = 'flask'
                result['project_type'] = 'web_api'
                result['suggested_port'] = 5000
            elif 'streamlit' in content_lower:
                result['framework'] = 'streamlit'
                result['project_type'] = 'web_app'
                result['suggested_port'] = 8501
        
        # Node.js detection
        elif 'package.json' in config_files:
            result['language'] = 'node'
            result['base_image'] = 'node:18-alpine'
            
            try:
                package_json = json.loads(config_files['package.json'])
                dependencies = package_json.get('dependencies', {})
                
                if 'express' in dependencies:
                    result['framework'] = 'express'
                    result['project_type'] = 'web_api'
                    result['suggested_port'] = 3000
                elif 'next' in dependencies:
                    result['framework'] = 'next'
                    result['project_type'] = 'web_app'
                    result['suggested_port'] = 3000
                elif 'react' in dependencies:
                    result['framework'] = 'react'
                    result['project_type'] = 'web_app'
                    result['suggested_port'] = 3000
                elif 'vue' in dependencies:
                    result['framework'] = 'vue'
                    result['project_type'] = 'web_app'
                    result['suggested_port'] = 8080
            except:
                pass
        
        # Java detection
        elif 'pom.xml' in config_files or 'build.gradle' in config_files:
            result['language'] = 'java'
            result['base_image'] = 'openjdk:17-jre-slim'
            result['suggested_port'] = 8080
            
            content = config_files.get('pom.xml', '') + config_files.get('build.gradle', '')
            if 'spring' in content.lower():
                result['framework'] = 'spring'
                result['project_type'] = 'web_api'
        
        # Go detection
        elif 'go.mod' in config_files:
            result['language'] = 'go'
            result['base_image'] = 'golang:1.21-alpine'
            result['suggested_port'] = 8080
        
        # Ruby detection
        elif 'Gemfile' in config_files:
            result['language'] = 'ruby'
            result['base_image'] = 'ruby:3.2-alpine'
            
            content = config_files.get('Gemfile', '').lower()
            if 'rails' in content:
                result['framework'] = 'rails'
                result['project_type'] = 'web_app'
                result['suggested_port'] = 3000
            elif 'sinatra' in content:
                result['framework'] = 'sinatra'
                result['project_type'] = 'web_api'
                result['suggested_port'] = 4567
        
        # PHP detection
        elif 'composer.json' in config_files:
            result['language'] = 'php'
            result['base_image'] = 'php:8.2-apache'
            result['suggested_port'] = 80
            
            try:
                composer = json.loads(config_files['composer.json'])
                require = composer.get('require', {})
                if 'laravel/framework' in require:
                    result['framework'] = 'laravel'
                    result['project_type'] = 'web_app'
            except:
                pass
        
        if result['language']:
            logger.info(f"✅ Fallback detected: {result['language']}/{result['framework']}")
        else:
            logger.warning("⚠️ Could not detect language")
            result['confidence'] = 0
        
        return result
    
    
    async def detect(self, project_path: str, min_confidence: int = 70) -> Dict:
        """
        Main detection method with automatic fallback
        
        Args:
            project_path: Path to project
            min_confidence: Minimum confidence to accept LLM result
            
        Returns:
            Detection result
        """
        
        # Try LLM detection first
        if self.model:
            try:
                result = await self.detect_with_llm(project_path)
                
                # Check confidence
                if result['confidence'] >= min_confidence:
                    logger.info(f"✅ Using LLM detection (confidence: {result['confidence']}%)")
                    return result
                else:
                    logger.warning(f"⚠️ Low LLM confidence ({result['confidence']}%), using fallback")
                    
            except Exception as e:
                logger.error(f"LLM detection failed: {e}, falling back to file-based detection")
        
        # Fallback to file-based detection
        return self.fallback_detection(project_path)


# Singleton instance
_detector = None

def get_detector(api_key: Optional[str] = None) -> LLMDetector:
    """Get or create detector instance"""
    global _detector
    if _detector is None:
        _detector = LLMDetector(api_key)
    return _detector
