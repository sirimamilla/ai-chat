"""Chat memory implementation using PostgreSQL backend."""

from typing import Any, Dict, List, Optional

from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.orm import Session

from .database import ChatMessage, get_db


class PostgreSQLChatMemory:
    """Chat memory backed by PostgreSQL for multi-user support."""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        db_session: Optional[Session] = None,
        max_messages: int = 50
    ):
        """Initialize chat memory.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
            db_session: Database session (if None, will create one)
            max_messages: Maximum number of messages to keep in memory
        """
        self.session_id = session_id
        self.user_id = user_id
        self.db_session = db_session
        self.max_messages = max_messages
        self._own_session = db_session is None

    def _get_session(self) -> Session:
        """Get or create database session."""
        if self.db_session is None:
            self.db_session = next(get_db())
        return self.db_session

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a message to the chat history.

        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata dictionary
        """
        db = self._get_session()

        message = ChatMessage(
            session_id=self.session_id,
            user_id=self.user_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        db.add(message)
        db.commit()

    def get_messages(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get chat messages for this session.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries
        """
        db = self._get_session()

        query = db.query(ChatMessage).filter(
            ChatMessage.session_id == self.session_id
        ).order_by(ChatMessage.created_at.desc())

        if limit:
            query = query.limit(limit)
        else:
            query = query.limit(self.max_messages)

        messages = query.all()

        # Reverse to get chronological order
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat()
            }
            for msg in reversed(messages)
        ]

    def get_langchain_messages(
        self,
        limit: Optional[int] = None
    ) -> List[BaseMessage]:
        """Get messages in LangChain format.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of LangChain message objects
        """
        messages = self.get_messages(limit)
        langchain_messages = []

        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))

        return langchain_messages

    def clear(self):
        """Clear all messages for this session."""
        db = self._get_session()
        db.query(ChatMessage).filter(
            ChatMessage.session_id == self.session_id
        ).delete()
        db.commit()

    def close(self):
        """Close database session if we own it."""
        if self._own_session and self.db_session:
            self.db_session.close()
            self.db_session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
