"""
AI Conversation Handler
Generates intelligent responses and questions using Gemini
"""

import json
import logging
from typing import Dict, List, Optional
from chat_manager import ConversationSession, get_questions_for_type

logger = logging.getLogger(__name__)


class ConversationAI:
    """Handles AI conversation logic"""
    
    def __init__(self, gemini_model):
        self.model = gemini_model
        logger.info("Conversation AI initialized")
    
    async def generate_response(
        self,
        session: ConversationSession,
        user_message: str
    ) -> Dict:
        """
        Generate AI response based on conversation state
        
        Returns:
        {
            'message': str,
            'options': List[Dict] or None,
            'complete': bool,
            'summary': Dict or None,
            'context_update': Dict
        }
        """
        # Get question templates
        questions = get_questions_for_type(session.conversation_type)
        
        # Check if we have more questions
        if session.current_question <= len(questions):
            return self._get_next_question(session, questions, user_message)
        else:
            # All questions answered - generate summary
            return await self._generate_summary(session)
    
    def _get_next_question(
        self,
        session: ConversationSession,
        questions: List[Dict],
        user_message: str
    ) -> Dict:
        """Get next question in flow"""
        
        # On first user message, try to extract information
        if session.current_question == 1:
            # Extract information from the first message
            extracted_info = self._extract_info_from_message(user_message, questions)
            
            # Store extracted info in context
            for key, value in extracted_info.items():
                session.context[key] = value
                logger.info(f"Extracted from first message: {key} = {value}")
        else:
            # Store user's answer in context for subsequent questions
            prev_question_id = questions[session.current_question - 2]['id']
            
            # Normalize the answer (handle both value and label)
            normalized_answer = self._normalize_answer(
                user_message, 
                questions[session.current_question - 2]
            )
            
            session.context[prev_question_id] = normalized_answer
            logger.info(f"Stored answer: {prev_question_id} = {normalized_answer}")
        
        # Find next unanswered question
        question_idx = session.current_question - 1
        
        # Skip questions that are already answered
        while question_idx < len(questions):
            question = questions[question_idx]
            question_id = question['id']
            
            # Check if this question is already answered
            if question_id not in session.context:
                break
            
            # This question is answered, move to next
            question_idx += 1
            session.current_question += 1
        
        if question_idx >= len(questions):
            # No more questions
            return {
                'message': "Great! Let me generate your infrastructure...",
                'options': None,
                'complete': True,
                'summary': None,
                'context_update': {}
            }
        
        question = questions[question_idx]
        
        # Format response
        message = question['question']
        
        # Add hints if available
        if 'hint' in question:
            message += f"\n\n💡 {question['hint']}"
        
        # Check if optional
        if question.get('optional'):
            message += "\n\n_(You can skip this if not needed)_"
        
        return {
            'message': message,
            'options': question.get('options'),
            'complete': False,
            'summary': None,
            'context_update': {}
        }
    
    def _normalize_answer(self, answer: str, question: Dict) -> str:
        """Normalize answer to match expected values"""
        answer_lower = answer.lower().strip()
        
        # If question has options, try to match to value
        if 'options' in question:
            for option in question['options']:
                # Check if answer matches the value exactly (e.g., "eks")
                if option['value'].lower() == answer_lower:
                    logger.info(f"Matched answer '{answer}' to value '{option['value']}'")
                    return option['value']
                
                # Check if answer matches the label (user clicked button text)
                if option['label'].lower() in answer_lower or answer_lower in option['label'].lower():
                    logger.info(f"Matched answer '{answer}' to label, returning value '{option['value']}'")
                    return option['value']
        
        # For platform specifically (extra safety)
        if question.get('id') == 'platform':
            if 'eks' in answer_lower or 'kubernetes' in answer_lower:
                logger.info(f"Platform answer normalized to 'eks' from '{answer}'")
                return 'eks'
            elif 'ecs' in answer_lower or 'fargate' in answer_lower:
                logger.info(f"Platform answer normalized to 'ecs' from '{answer}'")
                return 'ecs'
            elif 'ec2' in answer_lower:
                logger.info(f"Platform answer normalized to 'ec2' from '{answer}'")
                return 'ec2'
        
        # For traffic
        if question.get('id') == 'traffic':
            if 'low' in answer_lower:
                return 'low'
            elif 'medium' in answer_lower:
                return 'medium'
            elif 'high' in answer_lower:
                return 'high'
        
        # Return as-is if no normalization needed
        logger.info(f"No normalization needed for answer '{answer}'")
        return answer
    
    def _extract_info_from_message(self, message: str, questions: List[Dict]) -> Dict:
        """Extract information from user's message"""
        extracted = {}
        message_lower = message.lower()
        
        # Extract numbers (for count questions)
        import re
        numbers = re.findall(r'\b(\d+)\b', message)
        
        for question in questions:
            question_id = question['id']
            
            # Extract count/number
            if question_id == 'count' and numbers:
                extracted['count'] = numbers[0]
                logger.info(f"Extracted count: {numbers[0]}")
            
            # Extract platform mentions
            elif question_id == 'platform':
                if 'ecs' in message_lower or 'fargate' in message_lower:
                    extracted['platform'] = 'ecs'
                elif 'eks' in message_lower or 'kubernetes' in message_lower:
                    extracted['platform'] = 'eks'
                elif 'ec2' in message_lower and 'docker' in message_lower:
                    extracted['platform'] = 'ec2'
            
            # Extract traffic/scale mentions
            elif question_id == 'traffic':
                if 'high' in message_lower or 'large' in message_lower or 'heavy' in message_lower:
                    extracted['traffic'] = 'high'
                elif 'medium' in message_lower or 'moderate' in message_lower:
                    extracted['traffic'] = 'medium'
                elif 'low' in message_lower or 'small' in message_lower or 'light' in message_lower:
                    extracted['traffic'] = 'low'
            
            # Extract database mentions
            elif question_id in ['database', 'databases', 'db_type']:
                databases = []
                if 'mysql' in message_lower:
                    databases.append('mysql')
                if 'postgres' in message_lower or 'postgresql' in message_lower:
                    databases.append('postgresql')
                if 'mongo' in message_lower or 'mongodb' in message_lower:
                    databases.append('mongodb')
                if 'redis' in message_lower:
                    databases.append('redis')
                
                if databases:
                    if question['type'] == 'multiple':
                        extracted[question_id] = ', '.join(databases)
                    else:
                        extracted[question_id] = databases[0]
            
            # Extract availability mentions
            elif question_id == 'availability':
                if 'high availability' in message_lower or 'ha' in message_lower or 'multi-az' in message_lower or 'multi az' in message_lower:
                    extracted['availability'] = 'multi_az'
        
        return extracted
        
        # Check if optional
        if question.get('optional'):
            message += "\n\n_(You can skip this if not needed)_"
        
        return {
            'message': message,
            'options': question.get('options'),
            'complete': False,
            'summary': None,
            'context_update': {}
        }
    
    async def _generate_summary(self, session: ConversationSession) -> Dict:
        """Generate final summary and recommendations"""
        
        # Build context for AI
        context = self._build_context_summary(session)
        
        # Generate AI summary
        prompt = f"""Based on this conversation, create a comprehensive infrastructure summary:

Conversation History:
{session.get_conversation_history()}

User Requirements:
{json.dumps(session.context, indent=2)}

Generate a summary with:
1. What infrastructure will be created
2. Estimated monthly cost
3. Key features
4. Scaling capabilities

Format as friendly, clear text. Include emojis. Be specific about AWS services.
"""
        
        try:
            response = self.model.generate_content(prompt)
            summary_text = response.text
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            summary_text = "I'll create infrastructure based on your requirements!"
        
        # Build structured intent
        intent = self._build_intent_from_context(session)
        
        return {
            'message': summary_text + "\n\n**Ready to generate?**",
            'options': [
                {'value': 'yes', 'label': '✅ Yes, Generate Infrastructure!'},
                {'value': 'change', 'label': '✏️ Let me change something'},
            ],
            'complete': True,
            'summary': {
                'intent': intent,
                'context': session.context,
                'conversation_type': session.conversation_type
            },
            'context_update': {}
        }
    
    def _build_context_summary(self, session: ConversationSession) -> str:
        """Build readable context summary"""
        summary_parts = []
        
        for key, value in session.context.items():
            summary_parts.append(f"- {key}: {value}")
        
        return "\n".join(summary_parts)
    
    def _build_intent_from_context(self, session: ConversationSession) -> Dict:
        """Build structured intent from conversation context"""
        
        intent = {
            'resources': [],
            'region': 'us-east-1',
            'environment': 'production',
            'requirements': [],
            'constraints': [],
            'summary': '',
            'user_request': session.messages[0].content if session.messages else '',
            'conversation_context': session.context
        }
        
        # Extract resources based on conversation type
        if session.conversation_type == 'microservices':
            # Check which platform user selected
            platform = session.context.get('platform', 'ecs')
            logger.info(f"Building intent for microservices with platform: {platform}")
            logger.info(f"Full context: {session.context}")
            
            # Base networking resources
            intent['resources'].extend(['vpc', 'subnet', 'security_group'])
            
            # Platform-specific resources
            if platform == 'eks':
                # EKS (Kubernetes)
                logger.info("Adding EKS resources")
                intent['resources'].extend([
                    'eks_cluster',
                    'eks_node_group',
                    'iam_role',
                    'alb',
                    'target_group'
                ])
                intent['requirements'].append('EKS (Kubernetes) cluster')
            elif platform == 'ec2':
                # EC2 with Docker
                logger.info("Adding EC2 resources")
                intent['resources'].extend([
                    'ec2',
                    'launch_template',
                    'autoscaling_group',
                    'alb',
                    'target_group'
                ])
                intent['requirements'].append('EC2 instances with Docker')
            else:
                # ECS Fargate (default)
                logger.info(f"Adding ECS resources (platform={platform})")
                intent['resources'].extend([
                    'ecs',
                    'ecs_service',
                    'ecs_task_definition',
                    'alb',
                    'target_group'
                ])
                intent['requirements'].append('ECS Fargate cluster')
            
            # Add database if specified
            databases = session.context.get('databases', '')
            if 'mysql' in str(databases).lower():
                intent['resources'].append('rds')
            if 'redis' in str(databases).lower():
                intent['resources'].append('elasticache')
            if 'mongodb' in str(databases).lower():
                intent['resources'].append('documentdb')
            
            # Build requirements
            count = session.context.get('count', '5')
            platform = session.context.get('platform', 'ecs')
            intent['requirements'].append(f"{count} microservices")
            
            traffic = session.context.get('traffic', 'medium')
            intent['requirements'].append(f"{traffic} traffic")
            
            # Build summary with platform
            platform_names = {
                'eks': 'EKS (Kubernetes)',
                'ecs': 'ECS Fargate',
                'ec2': 'EC2 with Docker'
            }
            platform_name = platform_names.get(platform, 'ECS Fargate')
            intent['summary'] = f"Deploy {count} microservices on {platform_name} with {traffic} traffic"
        
        elif session.conversation_type == 'web_app':
            intent['resources'].extend(['vpc', 'subnet', 'ec2', 'alb', 'security_group'])
            
            # Add database if needed
            database = session.context.get('database', 'none')
            if database != 'none':
                intent['resources'].append('rds')
                intent['requirements'].append(f"{database} database")
            
            # Add S3 for static content
            intent['resources'].append('s3')
            
            traffic = session.context.get('traffic', 'medium')
            intent['requirements'].append(f"{traffic} traffic")
            
            app_type = session.context.get('app_type', 'dynamic')
            intent['summary'] = f"Deploy {app_type} web application"
        
        elif session.conversation_type == 'api':
            intent['resources'].extend(['api_gateway', 'lambda', 'security_group'])
            
            # Add database
            database = session.context.get('database', 'dynamodb')
            if database == 'dynamodb':
                intent['resources'].append('dynamodb')
            elif database == 'rds':
                intent['resources'].extend(['rds', 'vpc', 'subnet'])
            
            # Add auth if needed
            auth = session.context.get('auth', 'none')
            if auth == 'cognito':
                intent['resources'].append('cognito')
            
            api_type = session.context.get('api_type', 'rest')
            intent['summary'] = f"Deploy {api_type} API backend"
        
        elif session.conversation_type == 'database':
            intent['resources'].extend(['vpc', 'subnet', 'security_group'])
            
            db_type = session.context.get('db_type', 'mysql')
            if db_type in ['mysql', 'postgresql']:
                intent['resources'].append('rds')
            elif db_type == 'mongodb':
                intent['resources'].append('documentdb')
            elif db_type == 'redis':
                intent['resources'].append('elasticache')
            
            availability = session.context.get('availability', 'single')
            if availability == 'multi_az':
                intent['requirements'].append('Multi-AZ high availability')
            
            intent['summary'] = f"Deploy {db_type} database"
        
        elif session.conversation_type == 'data_pipeline':
            intent['resources'].extend(['s3', 'lambda', 'glue'])
            
            pipeline_type = session.context.get('pipeline_type', 'batch')
            if 'streaming' in pipeline_type:
                intent['resources'].append('kinesis')
            
            storage = session.context.get('storage', 's3')
            if 'redshift' in storage:
                intent['resources'].append('redshift')
            
            intent['summary'] = f"Deploy {pipeline_type} data pipeline"
        
        return intent


def format_options_message(options: List[Dict]) -> str:
    """Format options as readable text"""
    if not options:
        return ""
    
    lines = ["\n**Choose an option:**\n"]
    for i, opt in enumerate(options, 1):
        lines.append(f"{i}. {opt['label']}")
    
    return "\n".join(lines)