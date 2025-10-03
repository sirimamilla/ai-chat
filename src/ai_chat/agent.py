"""Main agent implementation using LangGraph and Vertex AI."""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from langchain_google_vertexai import ChatVertexAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .config import settings
from .memory import PostgreSQLChatMemory
from .tool_selector import ToolSelector

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agent graph."""

    messages: List[BaseMessage]
    user_input: str
    session_id: str
    user_id: str
    tools: List[Any]
    next_action: str


class ChatAgent:
    """Main chat agent with LangGraph orchestration."""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        tool_selector: ToolSelector,
        memory: Optional[PostgreSQLChatMemory] = None
    ):
        """Initialize chat agent.

        Args:
            session_id: Unique session identifier
            user_id: User identifier
            tool_selector: Tool selector instance
            memory: Optional chat memory instance
        """
        self.session_id = session_id
        self.user_id = user_id
        self.tool_selector = tool_selector

        # Initialize memory
        if memory is None:
            self.memory = PostgreSQLChatMemory(session_id, user_id)
        else:
            self.memory = memory

        # Initialize Vertex AI model
        self.llm = ChatVertexAI(
            model_name=settings.vertex_ai_model,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            temperature=0.7,
            max_output_tokens=2048,
        )

        # Build the agent graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for the agent."""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("load_tools", self._load_tools_node)
        workflow.add_node("call_model", self._call_model_node)
        workflow.add_node("execute_tools", ToolNode([]))  # Will be populated dynamically

        # Define edges
        workflow.set_entry_point("load_tools")
        workflow.add_edge("load_tools", "call_model")
        workflow.add_conditional_edges(
            "call_model",
            self._should_use_tools,
            {
                "tools": "execute_tools",
                "end": END
            }
        )
        workflow.add_edge("execute_tools", "call_model")

        return workflow.compile()

    async def _load_tools_node(self, state: AgentState) -> AgentState:
        """Load appropriate tools based on user input."""
        tools = await self.tool_selector.select_tools(state["user_input"])
        state["tools"] = tools
        logger.info(f"Loaded {len(tools)} tools for this request")
        return state

    async def _call_model_node(self, state: AgentState) -> AgentState:
        """Call the LLM with current state."""
        messages = state["messages"]

        # Bind tools to the model if available
        if state.get("tools"):
            llm_with_tools = self.llm.bind_tools(state["tools"])
            response = await llm_with_tools.ainvoke(messages)
        else:
            response = await self.llm.ainvoke(messages)

        # Add response to messages
        messages.append(response)
        state["messages"] = messages

        # Determine next action
        if hasattr(response, "tool_calls") and response.tool_calls:
            state["next_action"] = "tools"
        else:
            state["next_action"] = "end"

        return state

    def _should_use_tools(self, state: AgentState) -> str:
        """Determine if tools should be used."""
        return state.get("next_action", "end")

    async def chat(self, user_input: str) -> str:
        """Process a chat message.

        Args:
            user_input: User's message

        Returns:
            Agent's response
        """
        try:
            # Save user message to memory
            self.memory.add_message("user", user_input)

            # Get conversation history
            history = self.memory.get_langchain_messages(limit=10)

            # Add current user input
            history.append(HumanMessage(content=user_input))

            # Prepare initial state
            initial_state: AgentState = {
                "messages": history,
                "user_input": user_input,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "tools": [],
                "next_action": "load_tools"
            }

            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)

            # Get the assistant's response
            assistant_message = final_state["messages"][-1]
            response = assistant_message.content

            # Save assistant response to memory
            self.memory.add_message("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Error in chat processing: {e}", exc_info=True)
            error_message = f"I encountered an error: {str(e)}"
            self.memory.add_message("assistant", error_message)
            return error_message

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get chat history.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries
        """
        return self.memory.get_messages(limit)

    def clear_history(self):
        """Clear chat history for this session."""
        self.memory.clear()

    def close(self):
        """Clean up resources."""
        self.memory.close()
