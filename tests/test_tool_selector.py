"""Tests for tool selector module."""

import pytest
from src.ai_chat.tool_selector import ToolSelector
from src.ai_chat.mcp_client import MCPClient, MCPServerConfig


@pytest.fixture
def mock_servers():
    """Create mock MCP server configurations."""
    return [
        MCPServerConfig(
            name="filesystem",
            description="File operations",
            sse_endpoint="http://localhost:3000/sse",
            enabled=True,
            capabilities=["read_file", "write_file"]
        ),
        MCPServerConfig(
            name="database",
            description="Database operations",
            sse_endpoint="http://localhost:3001/sse",
            enabled=True,
            capabilities=["execute_query", "get_schema"]
        ),
        MCPServerConfig(
            name="web_search",
            description="Web search",
            sse_endpoint="http://localhost:3002/sse",
            enabled=False,  # Disabled
            capabilities=["search"]
        ),
    ]


@pytest.fixture
def tool_selector(mock_servers):
    """Create a tool selector instance."""
    mcp_client = MCPClient(mock_servers)
    config = {
        "keywords": {
            "filesystem": ["file", "directory", "folder"],
            "database": ["database", "query", "table"],
            "web_search": ["search", "web", "internet"]
        },
        "default_tools": ["filesystem"],
        "max_tools": 5
    }
    return ToolSelector(mcp_client, config)


def test_analyze_user_request_with_keywords(tool_selector):
    """Test analyzing user request with matching keywords."""
    # Test filesystem keywords
    servers = tool_selector.analyze_user_request("Can you read this file?")
    assert "filesystem" in servers

    # Test database keywords
    servers = tool_selector.analyze_user_request("Execute a database query")
    assert "database" in servers
    assert "filesystem" in servers  # Always includes default


def test_analyze_user_request_multiple_keywords(tool_selector):
    """Test analyzing request with multiple matching keywords."""
    servers = tool_selector.analyze_user_request(
        "Search the database and read the file"
    )
    assert "filesystem" in servers
    assert "database" in servers


def test_analyze_user_request_no_keywords(tool_selector):
    """Test analyzing request with no matching keywords."""
    servers = tool_selector.analyze_user_request("Hello, how are you?")
    # Should still include default tools
    assert "filesystem" in servers


def test_analyze_user_request_case_insensitive(tool_selector):
    """Test that keyword matching is case insensitive."""
    servers = tool_selector.analyze_user_request("Can you READ this FILE?")
    assert "filesystem" in servers


@pytest.mark.asyncio
async def test_select_tools(tool_selector):
    """Test selecting tools based on user input."""
    tools = await tool_selector.select_tools("Can you read this file?")

    # Should include filesystem tools
    assert len(tools) > 0
    tool_names = [tool.name for tool in tools]
    assert any("filesystem" in name for name in tool_names)


@pytest.mark.asyncio
async def test_select_tools_respects_max_tools(tool_selector):
    """Test that tool selection respects max_tools limit."""
    tools = await tool_selector.select_tools("Search database and file operations")

    # Should not exceed max_tools
    assert len(tools) <= tool_selector.max_tools


@pytest.mark.asyncio
async def test_select_tools_with_force_servers(tool_selector):
    """Test selecting tools with forced servers."""
    tools = await tool_selector.select_tools(
        "Some message",
        force_servers=["database"]
    )

    # Should include database tools
    tool_names = [tool.name for tool in tools]
    assert any("database" in name for name in tool_names)


@pytest.mark.asyncio
async def test_select_tools_disabled_server(tool_selector):
    """Test that disabled servers are not included."""
    # web_search is disabled in mock_servers
    tools = await tool_selector.select_tools("Search the web")

    # Should not include web_search tools (it's disabled)
    tool_names = [tool.name for tool in tools]
    assert not any("web_search" in name for name in tool_names)
