import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(64), unique=True, nullable=False)
    title = Column(String(255))
    chat_type = Column(String(32))
    username = Column(String(255))
    member_count = Column(Integer)
    is_forum = Column(Boolean, default=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Chat {self.chat_id}: {self.title}>'

class Database:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.connected = False
        
    def connect(self):
        """Initialize database connection"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                logger.warning("DATABASE_URL not found. Chat tracking disabled.")
                return False
                
            self.engine = create_engine(
                database_url,
                pool_recycle=300,
                pool_pre_ping=True,
                echo=False
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            self.connected = True
            logger.info("Database connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.connected = False
            return False
    
    def get_session(self) -> Session:
        """Get a database session"""
        if not self.connected:
            return None
        return self.SessionLocal()
    
    def update_chat_info(self, chat_id: str, title: str = None, chat_type: str = None, 
                        username: str = None, member_count: int = None, is_forum: bool = False):
        """Update or create chat information"""
        if not self.connected:
            return
            
        session = self.get_session()
        if not session:
            return
            
        try:
            # Try to find existing chat
            chat = session.query(Chat).filter(Chat.chat_id == str(chat_id)).first()
            
            if chat:
                # Update existing chat
                if title:
                    chat.title = title
                if chat_type:
                    chat.chat_type = chat_type
                if username:
                    chat.username = username
                if member_count is not None:
                    chat.member_count = member_count
                chat.is_forum = is_forum
                chat.last_activity = datetime.utcnow()
            else:
                # Create new chat
                chat = Chat(
                    chat_id=str(chat_id),
                    title=title,
                    chat_type=chat_type,
                    username=username,
                    member_count=member_count,
                    is_forum=is_forum,
                    first_seen=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )
                session.add(chat)
            
            session.commit()
            logger.debug(f"Updated chat info for {chat_id}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating chat {chat_id}: {e}")
            session.rollback()
        finally:
            session.close()

# Global database instance
db = Database()