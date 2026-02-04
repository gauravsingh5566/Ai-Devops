"""
Chat Manager for User-AI Conversation
Handles conversation state, message routing, and question flow
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Single chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    options: Optional[List[Dict]] = None
    

@dataclass
class ConversationSession:
    """Chat conversation session"""
    session_id: str
    user_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    current_question: int = 1
    total_questions: int = 5
    conversation_type: Optional[str] = None  # 'web_app', 'microservices', etc.
    created_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    
    def add_message(self, role: str, content: str, options: Optional[List[Dict]] = None):
        """Add message to conversation"""
        message = ChatMessage(role=role, content=content, options=options)
        self.messages.append(message)
        return message
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        history = []
        for msg in self.messages:
            prefix = "User: " if msg.role == "user" else "AI: "
            history.append(f"{prefix}{msg.content}")
        return "\n".join(history)


class ChatManager:
    """Manages chat conversations"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        logger.info("Chat Manager initialized")
    
    def create_session(self, user_id: str) -> ConversationSession:
        """Create new chat session"""
        session_id = str(uuid.uuid4())
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id
        )
        self.sessions[session_id] = session
        logger.info(f"Created chat session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def generate_greeting(self) -> str:
        """Generate initial greeting message"""
        return """Hi! 👋 I'm your DevOps assistant. I'll help you create the perfect infrastructure.

What would you like to deploy today?

**Quick options:**
• Web application
• Microservices
• API backend
• Database
• Data pipeline

Or just tell me in your own words what you need!"""
    
    def determine_conversation_type(self, user_message: str) -> str:
        """Determine conversation type from initial message"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['microservice', 'microservices', 'micro service']):
            return 'microservices'
        elif any(word in message_lower for word in ['web', 'website', 'web app', 'webapp']):
            return 'web_app'
        elif 'api' in message_lower:
            return 'api'
        elif any(word in message_lower for word in ['database', 'db', 'mysql', 'postgresql', 'mongo']):
            return 'database'
        elif any(word in message_lower for word in ['data', 'pipeline', 'etl', 'analytics']):
            return 'data_pipeline'
        else:
            return 'general'


# Question templates for different conversation types
QUESTION_TEMPLATES = {
    'web_app': [
        {
            'id': 'app_type',
            'question': "What type of web application are you building?",
            'options': [
                {'value': 'static', 'label': '📄 Static website (HTML/CSS/JS only)'},
                {'value': 'dynamic', 'label': '🔄 Dynamic web app (with backend)'},
                {'value': 'ecommerce', 'label': '🛒 E-commerce site'},
                {'value': 'blog', 'label': '📝 Blog/CMS'},
            ]
        },
        {
            'id': 'traffic',
            'question': "How many users do you expect per day?",
            'options': [
                {'value': 'small', 'label': '👥 < 1,000 users (Small)'},
                {'value': 'medium', 'label': '👥👥 1,000 - 10,000 users (Medium)'},
                {'value': 'large', 'label': '👥👥👥 10,000+ users (Large)'},
            ]
        },
        {
            'id': 'database',
            'question': "Do you need a database?",
            'options': [
                {'value': 'mysql', 'label': '🗄️ Yes - MySQL'},
                {'value': 'postgresql', 'label': '🗄️ Yes - PostgreSQL'},
                {'value': 'mongodb', 'label': '🗄️ Yes - MongoDB'},
                {'value': 'none', 'label': '❌ No database needed'},
            ]
        }
    ],
    
    'microservices': [
        {
            'id': 'count',
            'question': "How many microservices do you need?",
            'type': 'number',
            'placeholder': 'Enter number (e.g., 5, 10, 20)',
            'hint': 'Typical: 5-10 for medium apps, 20+ for large'
        },
        {
            'id': 'platform',
            'question': "Which container platform would you like to use?",
            'options': [
                {'value': 'ecs', 'label': '🚀 ECS Fargate (Serverless, Recommended)'},
                {'value': 'eks', 'label': '☸️ EKS (Kubernetes)'},
                {'value': 'ec2', 'label': '🖥️ EC2 with Docker'},
            ]
        },
        {
            'id': 'traffic',
            'question': "Expected traffic level?",
            'options': [
                {'value': 'low', 'label': '📊 Low (< 1K requests/min)'},
                {'value': 'medium', 'label': '📈 Medium (1K - 10K requests/min)'},
                {'value': 'high', 'label': '📊📊 High (10K+ requests/min)'},
            ]
        },
        {
            'id': 'databases',
            'question': "What databases do you need? (Select all that apply)",
            'type': 'multiple',
            'options': [
                {'value': 'mysql', 'label': '🗄️ MySQL'},
                {'value': 'postgresql', 'label': '🗄️ PostgreSQL'},
                {'value': 'mongodb', 'label': '🍃 MongoDB'},
                {'value': 'redis', 'label': '⚡ Redis (caching)'},
            ]
        },
        {
            'id': 'additional',
            'question': "Any additional requirements? (Optional)",
            'type': 'text',
            'placeholder': 'e.g., message queue, CDN, multi-region',
            'optional': True
        }
    ],
    
    'api': [
        {
            'id': 'api_type',
            'question': "What type of API?",
            'options': [
                {'value': 'rest', 'label': '🔄 REST API'},
                {'value': 'graphql', 'label': '📊 GraphQL API'},
                {'value': 'websocket', 'label': '🔌 WebSocket/Real-time'},
            ]
        },
        {
            'id': 'scale',
            'question': "Expected request volume?",
            'options': [
                {'value': 'low', 'label': '📊 Low (< 100 req/sec)'},
                {'value': 'medium', 'label': '📈 Medium (100 - 1000 req/sec)'},
                {'value': 'high', 'label': '📊📊 High (1000+ req/sec)'},
            ]
        },
        {
            'id': 'auth',
            'question': "Need authentication?",
            'options': [
                {'value': 'cognito', 'label': '🔐 Yes - AWS Cognito'},
                {'value': 'custom', 'label': '🔑 Yes - Custom JWT'},
                {'value': 'none', 'label': '❌ No authentication'},
            ]
        },
        {
            'id': 'database',
            'question': "Database preference?",
            'options': [
                {'value': 'dynamodb', 'label': '⚡ DynamoDB (Serverless)'},
                {'value': 'rds', 'label': '🗄️ RDS (MySQL/PostgreSQL)'},
                {'value': 'mongodb', 'label': '🍃 MongoDB'},
            ]
        }
    ],
    
    'database': [
        {
            'id': 'db_type',
            'question': "What type of database do you need?",
            'options': [
                {'value': 'mysql', 'label': '🗄️ MySQL'},
                {'value': 'postgresql', 'label': '🗄️ PostgreSQL'},
                {'value': 'mongodb', 'label': '🍃 MongoDB'},
                {'value': 'redis', 'label': '⚡ Redis'},
            ]
        },
        {
            'id': 'size',
            'question': "Expected database size?",
            'options': [
                {'value': 'small', 'label': '📦 Small (< 20GB)'},
                {'value': 'medium', 'label': '📦📦 Medium (20-100GB)'},
                {'value': 'large', 'label': '📦📦📦 Large (100GB+)'},
            ]
        },
        {
            'id': 'availability',
            'question': "High availability needed?",
            'options': [
                {'value': 'multi_az', 'label': '✅ Yes - Multi-AZ (Recommended for production)'},
                {'value': 'single', 'label': '❌ No - Single instance (Dev/Test)'},
            ]
        }
    ],
    
    'data_pipeline': [
        {
            'id': 'pipeline_type',
            'question': "What type of data pipeline?",
            'options': [
                {'value': 'batch', 'label': '📦 Batch processing'},
                {'value': 'streaming', 'label': '🌊 Real-time streaming'},
                {'value': 'both', 'label': '🔄 Both batch and streaming'},
            ]
        },
        {
            'id': 'volume',
            'question': "Daily data volume?",
            'options': [
                {'value': 'small', 'label': '📊 < 1GB/day'},
                {'value': 'medium', 'label': '📈 1GB - 100GB/day'},
                {'value': 'large', 'label': '📊📊 100GB+/day'},
            ]
        },
        {
            'id': 'storage',
            'question': "Where to store processed data?",
            'options': [
                {'value': 's3', 'label': '📦 S3 Data Lake'},
                {'value': 'redshift', 'label': '🗄️ Redshift (Data Warehouse)'},
                {'value': 'both', 'label': '🔄 Both S3 and Redshift'},
            ]
        }
    ],
    
    'general': [
        {
            'id': 'category',
            'question': "What category best describes what you need?",
            'options': [
                {'value': 'web_app', 'label': '🌐 Web Application'},
                {'value': 'microservices', 'label': '🔧 Microservices'},
                {'value': 'api', 'label': '🔌 API Backend'},
                {'value': 'database', 'label': '🗄️ Database'},
                {'value': 'data_pipeline', 'label': '📊 Data Pipeline'},
                {'value': 'other', 'label': '❓ Something else'},
            ]
        }
    ]
}


def get_questions_for_type(conversation_type: str) -> List[Dict]:
    """Get question templates for conversation type"""
    return QUESTION_TEMPLATES.get(conversation_type, QUESTION_TEMPLATES['general'])
