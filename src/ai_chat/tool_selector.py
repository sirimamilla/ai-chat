"""Dynamic tool selection based on user requests."""

import logging
from typing import Dict, List, Set

import yaml
from langchain.tools import BaseTool

from .config import settings
from .mcp_client import MCPClient, MCPServerConfig, MCPTool

logger = logging.getLogger(__name__)


class ToolSelector:
    """Dynamically select tools based on user requests."""

    def __init__(self, mcp_client: MCPClient, config: Dict):
        """Initialize tool selector.

        Args:
            mcp_client: MCP client instance
            config: Tool selection configuration from YAML
        """
        self.mcp_client = mcp_client
        self.config = config
        self.keywords = config.get("keywords", {})
        self.default_tools = config.get("default_tools", [])
        self.max_tools = config.get("max_tools", 5)

    def analyze_user_request(self, user_input: str) -> Set[str]:
        """Analyze user input to determine which tools might be needed.

        Args:
            user_input: User's message/request

        Returns:
            Set of server names that should be loaded
        """
        user_input_lower = user_input.lower()
        matched_servers = set()

        # Check keywords for each server
        for server_name, server_keywords in self.keywords.items():
            for keyword in server_keywords:
                if keyword.lower() in user_input_lower:
                    matched_servers.add(server_name)
                    break

        # Always include default tools
        matched_servers.update(self.default_tools)

        return matched_servers

    async def select_tools(
        self,
        user_input: str,
        force_servers: List[str] = None
    ) -> List[MCPTool]:
        """Select appropriate tools for the user request.

        Args:
            user_input: User's message/request
            force_servers: Optional list of server names to force include

        Returns:
            List of selected tools
        """
        # Determine which servers to use
        if force_servers:
            server_names = set(force_servers)
        else:
            server_names = self.analyze_user_request(user_input)

        logger.info(f"Selected servers for request: {server_names}")

        # Get tools from selected servers
        selected_tools = []
        for server_name in server_names:
            tools = await self.mcp_client.get_tools_for_server(server_name)
            selected_tools.extend(tools)

            # Respect max_tools limit
            if len(selected_tools) >= self.max_tools:
                selected_tools = selected_tools[:self.max_tools]
                break

        logger.info(f"Selected {len(selected_tools)} tools")
        return selected_tools

    @classmethod
    def from_config_file(cls, config_path: str = None) -> "ToolSelector":
        """Create tool selector from configuration file.

        Args:
            config_path: Path to MCP configuration YAML file

        Returns:
            ToolSelector instance
        """
        if config_path is None:
            config_path = settings.get_mcp_config_path()

        # Load MCP configuration
        with open(config_path, "r") as f:
            mcp_config = yaml.safe_load(f)

        # Parse server configurations
        servers = [
            MCPServerConfig(**server_config)
            for server_config in mcp_config.get("servers", [])
        ]

        # Create MCP client
        mcp_client = MCPClient(servers)

        # Get tool selection config
        tool_selection_config = mcp_config.get("tool_selection", {})

        return cls(mcp_client, tool_selection_config)
