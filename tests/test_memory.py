"""Tests for chat memory module."""

import pytest
import uuid
from src.ai_chat.memory import PostgreSQLChatMemory
from src.ai_chat.database import init_db, Base, engine


@pytest.fixture(scope="function")
def setup_database():
    """Set up test database."""
    # Initialize database
    init_db()
    yield
    # Clean up - drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def memory(setup_database):
    """Create a memory instance for testing."""
    session_id = str(uuid.uuid4())
    user_id = "test-user"
    mem = PostgreSQLChatMemory(session_id, user_id)
    yield mem
    mem.close()


def test_add_and_get_messages(memory):
    """Test adding and retrieving messages."""
    # Add messages
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")
    memory.add_message("user", "How are you?")

    # Get messages
    messages = memory.get_messages()

    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"


def test_get_messages_with_limit(memory):
    """Test retrieving messages with limit."""
    # Add multiple messages
    for i in range(10):
        memory.add_message("user", f"Message {i}")

    # Get with limit
    messages = memory.get_messages(limit=5)

    assert len(messages) == 5


def test_get_langchain_messages(memory):
    """Test getting messages in LangChain format."""
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi!")
    memory.add_message("system", "System message")

    lc_messages = memory.get_langchain_messages()

    assert len(lc_messages) == 3
    assert lc_messages[0].content == "Hello"
    assert lc_messages[1].content == "Hi!"
    assert lc_messages[2].content == "System message"


def test_clear_messages(memory):
    """Test clearing messages."""
    # Add messages
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi!")

    # Clear
    memory.clear()

    # Verify cleared
    messages = memory.get_messages()
    assert len(messages) == 0


def test_message_metadata(memory):
    """Test adding messages with metadata."""
    metadata = {"source": "test", "importance": "high"}
    memory.add_message("user", "Important message", metadata=metadata)

    messages = memory.get_messages()
    assert len(messages) == 1
    assert messages[0]["metadata"] == metadata


def test_multiple_sessions():
    """Test that messages are isolated by session."""
    session1 = str(uuid.uuid4())
    session2 = str(uuid.uuid4())

    memory1 = PostgreSQLChatMemory(session1, "user1")
    memory2 = PostgreSQLChatMemory(session2, "user2")

    # Add messages to different sessions
    memory1.add_message("user", "Session 1 message")
    memory2.add_message("user", "Session 2 message")

    # Verify isolation
    messages1 = memory1.get_messages()
    messages2 = memory2.get_messages()

    assert len(messages1) == 1
    assert len(messages2) == 1
    assert messages1[0]["content"] == "Session 1 message"
    assert messages2[0]["content"] == "Session 2 message"

    memory1.close()
    memory2.close()
