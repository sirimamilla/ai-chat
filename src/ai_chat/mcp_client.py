"""MCP SSE client for remote tool integration."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable

import httpx
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPTool(BaseTool):
    """LangChain tool wrapper for MCP remote tools."""

    name: str
    description: str
    server_name: str
    sse_endpoint: str
    capability: str
    args_schema: Optional[type[BaseModel]] = None

    async def _arun(self, *args, **kwargs) -> str:
        """Async execution of the tool."""
        return await self._execute_remote(*args, **kwargs)

    def _run(self, *args, **kwargs) -> str:
        """Sync execution wrapper."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new task
            return asyncio.create_task(self._execute_remote(*args, **kwargs))
        else:
            return loop.run_until_complete(self._execute_remote(*args, **kwargs))

    async def _execute_remote(self, *args, **kwargs) -> str:
        """Execute the remote MCP tool via SSE endpoint."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Prepare the request payload
                payload = {
                    "capability": self.capability,
                    "args": args,
                    "kwargs": kwargs
                }

                # Send request to SSE endpoint
                response = await client.post(
                    self.sse_endpoint,
                    json=payload,
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()

                result = response.json()
                return json.dumps(result.get("result", result))

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling MCP tool {self.name}: {e}")
            return f"Error: Failed to execute {self.name} - {str(e)}"
        except Exception as e:
            logger.error(f"Error calling MCP tool {self.name}: {e}")
            return f"Error: {str(e)}"


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    name: str
    description: str
    sse_endpoint: str
    enabled: bool = True
    capabilities: List[str] = Field(default_factory=list)


class MCPClient:
    """Client for managing MCP server connections and tools."""

    def __init__(self, servers: List[MCPServerConfig]):
        """Initialize MCP client with server configurations.

        Args:
            servers: List of MCP server configurations
        """
        self.servers = {server.name: server for server in servers if server.enabled}
        self._tools_cache: Dict[str, List[MCPTool]] = {}

    async def get_tools_for_server(self, server_name: str) -> List[MCPTool]:
        """Get all tools available from a specific server.

        Args:
            server_name: Name of the MCP server

        Returns:
            List of MCPTool instances
        """
        if server_name in self._tools_cache:
            return self._tools_cache[server_name]

        if server_name not in self.servers:
            logger.warning(f"Server {server_name} not found or not enabled")
            return []

        server = self.servers[server_name]
        tools = []

        for capability in server.capabilities:
            tool = MCPTool(
                name=f"{server_name}_{capability}",
                description=f"{server.description} - {capability}",
                server_name=server_name,
                sse_endpoint=server.sse_endpoint,
                capability=capability
            )
            tools.append(tool)

        self._tools_cache[server_name] = tools
        return tools

    async def get_all_tools(self) -> List[MCPTool]:
        """Get all tools from all enabled servers.

        Returns:
            List of all available MCPTool instances
        """
        all_tools = []
        for server_name in self.servers.keys():
            tools = await self.get_tools_for_server(server_name)
            all_tools.extend(tools)
        return all_tools

    async def get_tools_by_capability(
        self,
        capabilities: List[str]
    ) -> List[MCPTool]:
        """Get tools matching specific capabilities.

        Args:
            capabilities: List of capability names to filter by

        Returns:
            List of matching MCPTool instances
        """
        all_tools = await self.get_all_tools()
        return [
            tool for tool in all_tools
            if tool.capability in capabilities
        ]

    def clear_cache(self):
        """Clear the tools cache."""
        self._tools_cache.clear()
