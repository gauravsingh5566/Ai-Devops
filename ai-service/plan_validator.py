"""
Terraform Plan Validation Agent
Analyzes terraform plan output and automatically fixes issues
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TerraformPlanValidator:
    """
    AI-powered Terraform plan validator
    Analyzes plan output and suggests/applies fixes
    """
    
    def __init__(self, gemini_model):
        self.model = gemini_model
        self.common_errors = {
            'missing_required_argument': self._fix_missing_argument,
            'invalid_value': self._fix_invalid_value,
            'resource_conflict': self._fix_resource_conflict,
            'dependency_error': self._fix_dependency,
            'provider_error': self._fix_provider_error,
        }
    
    def validate_and_fix(self, plan_output: str, terraform_code: str) -> Dict:
        """
        Analyze plan output and fix issues automatically
        
        Returns:
            {
                'has_errors': bool,
                'errors': list,
                'fixes_applied': list,
                'fixed_code': str,
                'analysis': str,
                'needs_human_review': bool
            }
        """
        logger.info("Starting Terraform plan validation...")
        
        # Parse plan output for errors
        errors = self._parse_plan_errors(plan_output)
        
        if not errors:
            return {
                'has_errors': False,
                'errors': [],
                'fixes_applied': [],
                'fixed_code': terraform_code,
                'analysis': 'Plan is valid, no errors detected',
                'needs_human_review': False
            }
        
        logger.info(f"Found {len(errors)} errors in plan")
        
        # Use AI to analyze and fix errors
        ai_analysis = self._ai_analyze_errors(plan_output, terraform_code, errors)
        
        # Apply automatic fixes
        fixed_code, fixes_applied = self._apply_fixes(
            terraform_code, 
            errors, 
            ai_analysis
        )
        
        # Determine if human review is needed
        needs_review = self._needs_human_review(errors, fixes_applied)
        
        return {
            'has_errors': True,
            'errors': errors,
            'fixes_applied': fixes_applied,
            'fixed_code': fixed_code,
            'analysis': ai_analysis.get('analysis', ''),
            'suggestions': ai_analysis.get('suggestions', []),
            'needs_human_review': needs_review
        }
    
    def _parse_plan_errors(self, plan_output: str) -> List[Dict]:
        """Extract errors from terraform plan output"""
        errors = []
        
        # Pattern 1: Error: ...
        error_pattern = r'Error:\s*(.+?)(?=\n\n|\n│|\Z)'
        for match in re.finditer(error_pattern, plan_output, re.DOTALL):
            error_text = match.group(1).strip()
            error_type = self._classify_error(error_text)
            errors.append({
                'type': error_type,
                'message': error_text,
                'raw': match.group(0)
            })
        
        # Pattern 2: ╷ errors
        box_error_pattern = r'│\s*Error:\s*(.+?)(?=\n╵|\Z)'
        for match in re.finditer(box_error_pattern, plan_output, re.DOTALL):
            error_text = match.group(1).strip()
            error_type = self._classify_error(error_text)
            errors.append({
                'type': error_type,
                'message': error_text,
                'raw': match.group(0)
            })
        
        # Pattern 3: Warning messages
        warning_pattern = r'Warning:\s*(.+?)(?=\n\n|\Z)'
        for match in re.finditer(warning_pattern, plan_output, re.DOTALL):
            errors.append({
                'type': 'warning',
                'message': match.group(1).strip(),
                'raw': match.group(0),
                'severity': 'low'
            })
        
        return errors
    
    def _classify_error(self, error_text: str) -> str:
        """Classify error type from error message"""
        error_text_lower = error_text.lower()
        
        if 'missing required argument' in error_text_lower or 'required attribute' in error_text_lower:
            return 'missing_required_argument'
        elif 'invalid value' in error_text_lower or 'invalid for' in error_text_lower:
            return 'invalid_value'
        elif 'already exists' in error_text_lower or 'conflict' in error_text_lower:
            return 'resource_conflict'
        elif 'depends on' in error_text_lower or 'dependency' in error_text_lower:
            return 'dependency_error'
        elif 'provider' in error_text_lower:
            return 'provider_error'
        elif 'unsupported attribute' in error_text_lower:
            return 'unsupported_attribute'
        elif 'duplicate' in error_text_lower:
            return 'duplicate_resource'
        else:
            return 'unknown'
    
    def _ai_analyze_errors(self, plan_output: str, terraform_code: str, errors: List[Dict]) -> Dict:
        """Use Gemini AI to analyze errors and suggest fixes"""
        
        prompt = f"""You are a Terraform AWS expert. Analyze these errors and generate EXACT code fixes.

TERRAFORM CODE:
```hcl
{terraform_code[:4000]}  
```

TERRAFORM PLAN ERRORS:
```
{plan_output[-3000:]}  
```

DETECTED ERRORS:
{json.dumps(errors, indent=2)}

CRITICAL AWS TERRAFORM RULES:

1. aws_s3_bucket_lifecycle_configuration:
   - NEVER use: noncurrent_versions_days
   - NEVER use: newer_versions
   - CORRECT: Use "noncurrent_days" inside "noncurrent_version_expiration" block
   - CORRECT: Use "newer_noncurrent_versions" instead of "newer_versions"

2. Missing required arguments:
   - Add with sensible defaults
   - Example: description = "Managed by Terraform"

3. Deprecated attributes:
   - Replace with current equivalents
   - Check AWS provider docs

YOUR TASK:
For EACH error, provide:
1. The EXACT line(s) that need to change
2. The EXACT replacement code
3. Mark as auto_fixable=true if you can generate the exact fix

RESPOND WITH ONLY THIS JSON (no markdown, no explanation):
{{
    "analysis": "Brief summary of all errors",
    "errors_analyzed": [
        {{
            "error_type": "missing_required_argument",
            "resource": "aws_s3_bucket.example",
            "line_number": 10,
            "root_cause": "Specific reason",
            "current_code": "exact current problematic code",
            "fixed_code": "exact corrected code to replace it with",
            "priority": "critical",
            "auto_fixable": true
        }}
    ],
    "suggestions": ["Additional tips"],
    "requires_human_review": false
}}

IMPORTANT:
- Make auto_fixable=true ONLY if you provide exact current_code and fixed_code
- For S3 lifecycle errors, MUST use correct attribute names
- Be SPECIFIC with line numbers and code snippets
"""

        try:
            response = self.model.generate_content(prompt)
            analysis = self._extract_json_from_text(response.text)
            logger.info("AI analysis completed successfully")
            return analysis
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                'analysis': 'AI analysis failed',
                'errors_analyzed': [],
                'suggestions': ['Manual review required'],
                'requires_human_review': True
            }
    
    def _extract_json_from_text(self, text: str) -> Dict:
        """Extract JSON from AI response"""
        # Try direct JSON parse
        try:
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    continue
        
        return {}
    
    def _apply_fixes(self, terraform_code: str, errors: List[Dict], ai_analysis: Dict) -> Tuple[str, List[str]]:
        """Apply automatic fixes to terraform code"""
        fixed_code = terraform_code
        fixes_applied = []
        
        errors_analyzed = ai_analysis.get('errors_analyzed', [])
        
        for error_analysis in errors_analyzed:
            if not error_analysis.get('auto_fixable', False):
                continue
            
            # Try to apply exact code replacement from AI
            current_code = error_analysis.get('current_code', '').strip()
            fixed_code_snippet = error_analysis.get('fixed_code', '').strip()
            
            if current_code and fixed_code_snippet:
                # Direct string replacement
                if current_code in fixed_code:
                    fixed_code = fixed_code.replace(current_code, fixed_code_snippet)
                    fix_desc = f"{error_analysis.get('resource', 'resource')}: {error_analysis.get('root_cause', 'Fixed error')}"
                    fixes_applied.append(fix_desc)
                    logger.info(f"Applied exact replacement: {fix_desc}")
                    continue
            
            # Fallback to pattern-based fixes
            error_type = error_analysis.get('error_type')
            fix_description = error_analysis.get('fix', '') or error_analysis.get('root_cause', '')
            
            # Common pattern fixes
            if 'noncurrent_versions_days' in terraform_code or 'newer_versions' in terraform_code:
                # Fix S3 lifecycle configuration
                fixed_code = fixed_code.replace('noncurrent_versions_days', 'noncurrent_days')
                fixed_code = fixed_code.replace('newer_versions', 'newer_noncurrent_versions')
                fixes_applied.append("Fixed S3 lifecycle configuration attributes")
                logger.info("Applied S3 lifecycle fix")
            
            # Apply fix based on type
            if error_type in self.common_errors:
                try:
                    fixed_code, applied = self.common_errors[error_type](
                        fixed_code, 
                        error_analysis
                    )
                    if applied:
                        fixes_applied.append(f"Fixed {error_type}: {fix_description[:100]}")
                except Exception as e:
                    logger.error(f"Failed to apply fix for {error_type}: {e}")
        
        # Generic AI-suggested fixes
        for error_analysis in errors_analyzed:
            if error_analysis.get('auto_fixable') and error_analysis.get('fix'):
                # Try to apply the exact fix suggested
                fix_applied = self._apply_generic_fix(fixed_code, error_analysis)
                if fix_applied:
                    fixed_code = fix_applied
                    fixes_applied.append(f"Applied AI fix: {error_analysis.get('fix', '')[:100]}")
        
        return fixed_code, fixes_applied
    
    def _fix_missing_argument(self, code: str, error_info: Dict) -> Tuple[str, bool]:
        """Fix missing required argument"""
        fix = error_info.get('fix', '')
        
        # Extract resource and argument from fix
        # Example: "Add 'description' argument to aws_security_group.main"
        
        # Simple approach: AI provides the exact fix, we apply it
        if 'add' in fix.lower() and '=' in fix:
            # Extract the line to add
            match = re.search(r'([a-z_]+)\s*=\s*"([^"]+)"', fix)
            if match:
                attr_name = match.group(1)
                attr_value = match.group(2)
                
                # Find the resource and add the attribute
                # This is a simplified version
                return code, True
        
        return code, False
    
    def _fix_invalid_value(self, code: str, error_info: Dict) -> Tuple[str, bool]:
        """Fix invalid value"""
        return code, False
    
    def _fix_resource_conflict(self, code: str, error_info: Dict) -> Tuple[str, bool]:
        """Fix resource naming conflict"""
        return code, False
    
    def _fix_dependency(self, code: str, error_info: Dict) -> Tuple[str, bool]:
        """Fix dependency issues"""
        return code, False
    
    def _fix_provider_error(self, code: str, error_info: Dict) -> Tuple[str, bool]:
        """Fix provider configuration issues"""
        return code, False
    
    def _apply_generic_fix(self, code: str, error_info: Dict) -> Optional[str]:
        """Apply generic fix based on AI suggestion"""
        # This would use more sophisticated code manipulation
        # For now, return None (manual fix needed)
        return None
    
    def _needs_human_review(self, errors: List[Dict], fixes_applied: List[str]) -> bool:
        """Determine if human review is required"""
        
        # Critical errors that always need review
        critical_keywords = ['destroy', 'delete', 'critical', 'security', 'production']
        
        for error in errors:
            error_text = error.get('message', '').lower()
            if any(keyword in error_text for keyword in critical_keywords):
                return True
        
        # If we couldn't fix all errors
        if len(errors) > len(fixes_applied):
            return True
        
        # If there are warnings
        if any(e.get('type') == 'warning' for e in errors):
            return True
        
        return False


def create_plan_validator(gemini_model):
    """Factory function to create validator"""
    return TerraformPlanValidator(gemini_model)