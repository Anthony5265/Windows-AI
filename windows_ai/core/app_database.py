"""
Application Database Layer

Provides persistent storage for:
- Plugin states and configurations
- User preferences and settings
- Conversation history
- System configuration
- Query history and analytics
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager

try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, scoped_session
    from sqlalchemy.pool import StaticPool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("Warning: SQLAlchemy not available, database functionality will be limited")

logger = logging.getLogger(__name__)

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class User(Base):
        """User accounts"""
        __tablename__ = 'users'
        
        id = Column(Integer, primary_key=True)
        username = Column(String(255), unique=True, nullable=False)
        email = Column(String(255), unique=True)
        created_at = Column(DateTime, default=datetime.now)
        last_login = Column(DateTime)
        preferences = Column(JSON, default=dict)
        is_active = Column(Boolean, default=True)
        
        # Relationships
        conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
        settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")

    class Conversation(Base):
        """Conversation/chat history"""
        __tablename__ = 'conversations'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
        title = Column(String(500))
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
        model = Column(String(100))
        extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
        
        # Relationships
        user = relationship("User", back_populates="conversations")
        messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    class Message(Base):
        """Individual messages in conversations"""
        __tablename__ = 'messages'
        
        id = Column(Integer, primary_key=True)
        conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
        role = Column(String(50), nullable=False)  # user, assistant, system
        content = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.now)
        tokens = Column(Integer)
        extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved by SQLAlchemy)
        
        # Relationships
        conversation = relationship("Conversation", back_populates="messages")

    class PluginState(Base):
        """Plugin runtime state"""
        __tablename__ = 'plugin_states'
        
        id = Column(Integer, primary_key=True)
        plugin_id = Column(String(255), unique=True, nullable=False)
        state = Column(String(50), nullable=False)  # enabled, disabled, error, etc.
        version = Column(String(50))
        config = Column(JSON, default=dict)
        last_error = Column(Text)
        last_used = Column(DateTime)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class UserSetting(Base):
        """User-specific settings"""
        __tablename__ = 'user_settings'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
        key = Column(String(255), nullable=False)
        value = Column(Text)
        value_type = Column(String(50))  # string, int, bool, json
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
        
        # Relationships
        user = relationship("User", back_populates="settings")

    class SystemConfig(Base):
        """System-wide configuration"""
        __tablename__ = 'system_config'
        
        id = Column(Integer, primary_key=True)
        key = Column(String(255), unique=True, nullable=False)
        value = Column(Text)
        value_type = Column(String(50))
        description = Column(Text)
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    class QueryHistory(Base):
        """Query history for analytics"""
        __tablename__ = 'query_history'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        query = Column(Text, nullable=False)
        plugin_id = Column(String(255))
        response_time = Column(Integer)  # milliseconds
        success = Column(Boolean, default=True)
        error_message = Column(Text)
        created_at = Column(DateTime, default=datetime.now)
        metadata = Column(JSON, default=dict)


class ApplicationDatabase:
    """
    Application database manager
    
    Provides high-level interface for database operations
    """
    
    def __init__(self, db_path: Optional[Path] = None, echo: bool = False):
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy is required for database functionality")
        
        self.db_path = db_path or Path.home() / ".windows_ai" / "app.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(
            db_url,
            echo=echo,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        
        logger.info(f"Application database initialized at {self.db_path}")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    # User management
    
    def create_user(self, username: str, email: Optional[str] = None) -> Optional[int]:
        """Create a new user"""
        try:
            with self.session_scope() as session:
                user = User(username=username, email=email)
                session.add(user)
                session.flush()
                return user.id
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    return {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'created_at': user.created_at.isoformat() if user.created_at else None,
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                        'preferences': user.preferences,
                        'is_active': user.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(username=username).first()
                if user:
                    return {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'created_at': user.created_at.isoformat() if user.created_at else None,
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                        'preferences': user.preferences,
                        'is_active': user.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            with self.session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    user.last_login = datetime.now()
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
    
    # Conversation management
    
    def create_conversation(
        self,
        user_id: int,
        title: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """Create a new conversation"""
        try:
            with self.session_scope() as session:
                conversation = Conversation(
                    user_id=user_id,
                    title=title or "New Conversation",
                    model=model,
                    metadata=metadata or {}
                )
                session.add(conversation)
                session.flush()
                return conversation.id
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return None
    
    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """Add a message to a conversation"""
        try:
            with self.session_scope() as session:
                message = Message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    tokens=tokens,
                    metadata=metadata or {}
                )
                session.add(message)
                session.flush()
                
                # Update conversation timestamp
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    conversation.updated_at = datetime.now()
                
                return message.id
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return None
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get conversation with messages"""
        try:
            with self.session_scope() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    return {
                        'id': conversation.id,
                        'user_id': conversation.user_id,
                        'title': conversation.title,
                        'model': conversation.model,
                        'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
                        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
                        'metadata': conversation.metadata,
                        'messages': [
                            {
                                'id': msg.id,
                                'role': msg.role,
                                'content': msg.content,
                                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                                'tokens': msg.tokens,
                                'metadata': msg.metadata
                            }
                            for msg in conversation.messages
                        ]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    def list_conversations(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """List user's conversations"""
        try:
            with self.session_scope() as session:
                conversations = session.query(Conversation).filter_by(user_id=user_id).order_by(
                    Conversation.updated_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'id': conv.id,
                        'title': conv.title,
                        'model': conv.model,
                        'created_at': conv.created_at.isoformat() if conv.created_at else None,
                        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                        'message_count': len(conv.messages)
                    }
                    for conv in conversations
                ]
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation"""
        try:
            with self.session_scope() as session:
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    session.delete(conversation)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    # Plugin state management
    
    def save_plugin_state(
        self,
        plugin_id: str,
        state: str,
        version: Optional[str] = None,
        config: Optional[Dict] = None,
        last_error: Optional[str] = None
    ) -> bool:
        """Save or update plugin state"""
        try:
            with self.session_scope() as session:
                plugin_state = session.query(PluginState).filter_by(plugin_id=plugin_id).first()
                
                if plugin_state:
                    plugin_state.state = state
                    if version:
                        plugin_state.version = version
                    if config is not None:
                        plugin_state.config = config
                    if last_error is not None:
                        plugin_state.last_error = last_error
                    plugin_state.updated_at = datetime.now()
                else:
                    plugin_state = PluginState(
                        plugin_id=plugin_id,
                        state=state,
                        version=version,
                        config=config or {},
                        last_error=last_error
                    )
                    session.add(plugin_state)
                
                return True
        except Exception as e:
            logger.error(f"Failed to save plugin state: {e}")
            return False
    
    def get_plugin_state(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin state"""
        try:
            with self.session_scope() as session:
                plugin_state = session.query(PluginState).filter_by(plugin_id=plugin_id).first()
                if plugin_state:
                    return {
                        'plugin_id': plugin_state.plugin_id,
                        'state': plugin_state.state,
                        'version': plugin_state.version,
                        'config': plugin_state.config,
                        'last_error': plugin_state.last_error,
                        'last_used': plugin_state.last_used.isoformat() if plugin_state.last_used else None,
                        'created_at': plugin_state.created_at.isoformat() if plugin_state.created_at else None,
                        'updated_at': plugin_state.updated_at.isoformat() if plugin_state.updated_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get plugin state: {e}")
            return None
    
    # Settings management
    
    def set_system_config(self, key: str, value: Any, value_type: str = "string", description: Optional[str] = None) -> bool:
        """Set system configuration value"""
        try:
            with self.session_scope() as session:
                config = session.query(SystemConfig).filter_by(key=key).first()
                
                if config:
                    config.value = str(value)
                    config.value_type = value_type
                    if description:
                        config.description = description
                    config.updated_at = datetime.now()
                else:
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        value_type=value_type,
                        description=description
                    )
                    session.add(config)
                
                return True
        except Exception as e:
            logger.error(f"Failed to set system config: {e}")
            return False
    
    def get_system_config(self, key: str) -> Optional[Any]:
        """Get system configuration value"""
        try:
            with self.session_scope() as session:
                config = session.query(SystemConfig).filter_by(key=key).first()
                if config:
                    # Convert based on type
                    if config.value_type == "int":
                        return int(config.value)
                    elif config.value_type == "bool":
                        return config.value.lower() in ('true', '1', 'yes')
                    elif config.value_type == "json":
                        import json
                        return json.loads(config.value)
                    else:
                        return config.value
                return None
        except Exception as e:
            logger.error(f"Failed to get system config: {e}")
            return None
    
    # Query history
    
    def log_query(
        self,
        query: str,
        user_id: Optional[int] = None,
        plugin_id: Optional[str] = None,
        response_time: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Log a query for analytics"""
        try:
            with self.session_scope() as session:
                history = QueryHistory(
                    user_id=user_id,
                    query=query,
                    plugin_id=plugin_id,
                    response_time=response_time,
                    success=success,
                    error_message=error_message,
                    metadata=metadata or {}
                )
                session.add(history)
                return True
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            return False
    
    def get_query_stats(self, user_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
        """Get query statistics"""
        try:
            from datetime import timedelta
            from sqlalchemy import func
            
            with self.session_scope() as session:
                since = datetime.now() - timedelta(days=days)
                
                query = session.query(QueryHistory).filter(QueryHistory.created_at >= since)
                if user_id:
                    query = query.filter_by(user_id=user_id)
                
                total_queries = query.count()
                successful_queries = query.filter_by(success=True).count()
                avg_response_time = query.with_entities(
                    func.avg(QueryHistory.response_time)
                ).scalar()
                
                return {
                    'total_queries': total_queries,
                    'successful_queries': successful_queries,
                    'failed_queries': total_queries - successful_queries,
                    'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                    'avg_response_time_ms': int(avg_response_time) if avg_response_time else 0
                }
        except Exception as e:
            logger.error(f"Failed to get query stats: {e}")
            return {}
    
    def close(self):
        """Close database connections"""
        self.Session.remove()
        self.engine.dispose()
        logger.info("Application database closed")
