"""Example usage of AI Chat programmatically."""

import asyncio
import uuid
from pathlib import Path
import sys

# Add parent directory to path to import ai_chat
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_chat.agent import ChatAgent
from src.ai_chat.database import init_db
from src.ai_chat.tool_selector import ToolSelector


async def main():
    """Example of using AI Chat programmatically."""
    # Initialize database
    print("Initializing database...")
    init_db()

    # Create tool selector
    print("Loading tool selector...")
    tool_selector = ToolSelector.from_config_file()

    # Create a session
    session_id = str(uuid.uuid4())
    user_id = "example-user"

    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")

    # Create agent
    agent = ChatAgent(
        session_id=session_id,
        user_id=user_id,
        tool_selector=tool_selector
    )

    # Example conversations
    conversations = [
        "Hello! Can you help me?",
        "What can you do?",
        "Can you search for information about Python programming?",
    ]

    print("\n" + "=" * 60)
    print("Starting conversation...")
    print("=" * 60 + "\n")

    for user_message in conversations:
        print(f"User: {user_message}")

        # Get response
        response = await agent.chat(user_message)

        print(f"Assistant: {response}\n")

    # Get conversation history
    print("=" * 60)
    print("Conversation History:")
    print("=" * 60)

    history = agent.get_history()
    for msg in history:
        print(f"{msg['role'].upper()}: {msg['content'][:100]}...")

    # Cleanup
    agent.close()
    print("\nSession closed.")


if __name__ == "__main__":
    asyncio.run(main())
