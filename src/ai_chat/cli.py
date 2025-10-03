"""Command-line interface for AI Chat."""

import asyncio
import logging
import uuid
from typing import Optional

import click

from .agent import ChatAgent
from .config import settings
from .database import init_db
from .memory import PostgreSQLChatMemory
from .tool_selector import ToolSelector

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """AI Chat - Agentic AI chat tool with Vertex AI and MCP integration."""
    pass


@cli.command()
@click.option("--user-id", default="cli-user", help="User identifier")
@click.option("--session-id", default=None, help="Session identifier (will be generated if not provided)")
def chat(user_id: str, session_id: Optional[str]):
    """Start an interactive chat session."""
    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
        logger.info(f"Generated session ID: {session_id}")

    # Initialize tool selector
    try:
        tool_selector = ToolSelector.from_config_file()
        logger.info("Tool selector initialized")
    except Exception as e:
        logger.error(f"Failed to initialize tool selector: {e}")
        click.echo("Error: Could not initialize tool selector. Check your configuration.")
        return

    # Create agent
    agent = ChatAgent(
        session_id=session_id,
        user_id=user_id,
        tool_selector=tool_selector
    )

    click.echo("=" * 60)
    click.echo("AI Chat - Interactive Session")
    click.echo("=" * 60)
    click.echo(f"User ID: {user_id}")
    click.echo(f"Session ID: {session_id}")
    click.echo("Type 'quit' or 'exit' to end the session")
    click.echo("Type 'history' to view conversation history")
    click.echo("Type 'clear' to clear conversation history")
    click.echo("=" * 60)

    # Main chat loop
    async def run_chat():
        while True:
            try:
                user_input = click.prompt("\nYou", type=str)

                if user_input.lower() in ["quit", "exit"]:
                    click.echo("Goodbye!")
                    break
                elif user_input.lower() == "history":
                    history = agent.get_history()
                    click.echo("\n--- Chat History ---")
                    for msg in history:
                        click.echo(f"{msg['role'].upper()}: {msg['content']}")
                    click.echo("--- End of History ---")
                    continue
                elif user_input.lower() == "clear":
                    agent.clear_history()
                    click.echo("History cleared.")
                    continue

                # Get response from agent
                response = await agent.chat(user_input)
                click.echo(f"\nAssistant: {response}")

            except KeyboardInterrupt:
                click.echo("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}", exc_info=True)
                click.echo(f"Error: {e}")

        # Cleanup
        agent.close()

    # Run the async chat loop
    asyncio.run(run_chat())


@cli.command()
@click.option("--host", default=None, help="API host")
@click.option("--port", default=None, type=int, help="API port")
def serve(host: Optional[str], port: Optional[int]):
    """Start the API server."""
    import uvicorn
    from .api import app

    # Use settings defaults if not provided
    host = host or settings.api_host
    port = port or settings.api_port

    click.echo(f"Starting AI Chat API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


@cli.command()
def init_database():
    """Initialize the database schema."""
    try:
        init_db()
        click.echo("Database initialized successfully!")
    except Exception as e:
        click.echo(f"Error initializing database: {e}")
        logger.error(f"Database initialization error: {e}", exc_info=True)


@cli.command()
def check_config():
    """Check configuration and display settings."""
    click.echo("=" * 60)
    click.echo("AI Chat Configuration")
    click.echo("=" * 60)
    click.echo(f"Project: {settings.google_cloud_project}")
    click.echo(f"Location: {settings.google_cloud_location}")
    click.echo(f"Model: {settings.vertex_ai_model}")
    click.echo(f"Database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    click.echo(f"MCP Config: {settings.mcp_config_path}")
    click.echo(f"API: {settings.api_host}:{settings.api_port}")
    click.echo("=" * 60)

    # Check if MCP config file exists
    config_path = settings.get_mcp_config_path()
    if config_path.exists():
        click.echo(f"✓ MCP config file found: {config_path}")
    else:
        click.echo(f"✗ MCP config file not found: {config_path}")


if __name__ == "__main__":
    cli()
