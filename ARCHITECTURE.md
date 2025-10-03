# Architecture Overview

This document provides a detailed overview of the AI Chat architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                           │
│  ┌──────────┐    ┌──────────┐    ┌────────────────────┐    │
│  │   CLI    │    │ REST API │    │  Python Library    │    │
│  └──────────┘    └──────────┘    └────────────────────┘    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    Application Layer                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   Chat Agent (LangGraph)                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │  Model   │  │   Tool   │  │    Chat Memory       │ │ │
│  │  │  (LLM)   │  │ Selector │  │   (PostgreSQL)       │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Integration Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Vertex AI   │  │  MCP Client  │  │   PostgreSQL     │  │
│  │   (Gemini)   │  │  (SSE/HTTP)  │  │   (RAG + State)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   External Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Google     │  │ MCP Servers  │  │    Database      │  │
│  │  Cloud AI    │  │  (Tools)     │  │    Server        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Chat Agent (`agent.py`)

The main orchestrator using LangGraph for workflow management.

**Responsibilities:**
- Orchestrate conversation flow
- Manage tool execution
- Coordinate with LLM
- Handle state transitions

**LangGraph Workflow:**
```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌────────────┐
│ Load Tools │ (Dynamic selection based on user input)
└─────┬──────┘
      │
      ▼
┌──────────────┐
│  Call Model  │ (Vertex AI Gemini)
└──────┬───────┘
       │
       ▼
    ┌──────┐
    │Tools?│
    └──┬───┘
       │
   Yes │           No
       ▼            │
┌──────────────┐    │
│Execute Tools │    │
└──────┬───────┘    │
       │            │
       └────────────┘
                    ▼
                 ┌─────┐
                 │ End │
                 └─────┘
```

### 2. Tool Selector (`tool_selector.py`)

Dynamically selects appropriate tools based on user input.

**Algorithm:**
1. Parse user input for keywords
2. Match keywords to MCP servers
3. Include default tools
4. Respect max_tools limit
5. Return filtered tool list

**Example:**
```
User Input: "Can you read the config file?"
           ↓
Keywords: ["read", "file"]
           ↓
Matched: filesystem server
           ↓
Tools: [filesystem_read_file, filesystem_write_file, ...]
```

### 3. MCP Client (`mcp_client.py`)

Interfaces with remote MCP servers via SSE endpoints.

**Features:**
- HTTP/SSE communication
- Tool caching
- Error handling
- Async execution

**Communication Flow:**
```
┌──────────┐    HTTP POST     ┌────────────┐
│   Agent  │ ───────────────► │ MCP Server │
│          │                  │  (Remote)  │
│          │ ◄─────────────── │            │
└──────────┘    JSON Result   └────────────┘
```

### 4. Chat Memory (`memory.py`)

PostgreSQL-backed memory for persistent conversations.

**Features:**
- Per-session storage
- Per-user isolation
- Message history
- LangChain integration

**Database Schema:**
```sql
chat_messages (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
)
```

### 5. Database Layer (`database.py`)

PostgreSQL models and connection management.

**Tables:**
- `chat_messages`: Conversation history
- `rag_documents`: RAG document store
- `user_sessions`: Session management

**Connection Pooling:**
- Pool size: 10
- Max overflow: 20
- Pre-ping: Enabled
- Recycle: 1 hour

## Data Flow

### Chat Request Flow

```
1. User sends message
   ↓
2. API receives request
   ↓
3. Get/create session
   ↓
4. Initialize agent with:
   - Session ID
   - User ID
   - Tool selector
   - Memory
   ↓
5. Agent processes message:
   a. Save to memory
   b. Load conversation history
   c. Select tools dynamically
   d. Call LLM with tools
   e. Execute tools if needed
   f. Get final response
   ↓
6. Save response to memory
   ↓
7. Return to user
```

## Multi-User Support

### Session Isolation

Each user conversation is isolated by:
- Unique `session_id`
- User-specific `user_id`
- Database-level filtering

```
User A (session_1) ─┐
                    ├─► PostgreSQL ─► Separate histories
User B (session_2) ─┘
```

### Concurrency

- Database connection pooling
- Stateless API design
- No shared memory between requests
- Thread-safe operations

## Multi-Instance Deployment

### Horizontal Scaling

```
        ┌─────────────┐
        │Load Balancer│
        └──────┬──────┘
               │
       ┌───────┼───────┐
       │       │       │
   ┌───▼──┐ ┌──▼──┐ ┌─▼───┐
   │API #1│ │API #2│ │API #3│
   └───┬──┘ └──┬──┘ └─┬───┘
       │       │       │
       └───────┼───────┘
               │
        ┌──────▼──────┐
        │  PostgreSQL │
        │  (Shared)   │
        └─────────────┘
```

**Key Features:**
- Stateless API instances
- Shared PostgreSQL state
- Any instance can handle any request
- Connection pooling per instance

## Security Considerations

### Authentication
- User ID passed with each request
- Session validation
- (TODO: Add JWT/OAuth)

### Database
- Connection pooling
- Parameterized queries
- No SQL injection risk

### API
- CORS enabled (configure for production)
- Input validation via Pydantic
- Error handling

## Performance Optimization

### Caching
- Tool definitions cached per server
- Database connection pooling
- (TODO: Add Redis for session cache)

### Database
- Indexed columns:
  - session_id
  - user_id
  - created_at
- Composite indexes for common queries
- JSONB for flexible metadata

### LLM Optimization
- Conversation history limited to recent messages
- Tool selection reduces context size
- Streaming support (future)

## Monitoring & Observability

### LangSmith Integration
- Trace all LLM calls
- Monitor tool usage
- Debug conversation flows
- Performance metrics

### Logging
- Structured logging
- Configurable log levels
- Request/response logging
- Error tracking

## Extension Points

### Adding New Tools
1. Deploy MCP server
2. Add to `config/mcp_servers.yaml`
3. Configure keywords for selection
4. Restart application

### Custom Memory Backend
Implement interface:
```python
class CustomMemory:
    def add_message(self, role, content, metadata)
    def get_messages(self, limit)
    def get_langchain_messages(self, limit)
    def clear()
```

### Alternative LLM
Replace in `agent.py`:
```python
from langchain_openai import ChatOpenAI
self.llm = ChatOpenAI(model="gpt-4")
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| LLM | Vertex AI (Gemini) | Language understanding |
| Framework | LangChain | LLM orchestration |
| Workflow | LangGraph | Agent state management |
| Database | PostgreSQL | Persistence & RAG |
| API | FastAPI | REST endpoints |
| CLI | Click | Command-line interface |
| Config | Pydantic | Settings management |
| HTTP | httpx | Async HTTP client |

## Future Enhancements

- [ ] Redis caching layer
- [ ] Streaming responses
- [ ] RAG document ingestion
- [ ] Vector search with pgvector
- [ ] WebSocket support
- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] Metrics dashboard
- [ ] Multi-model support
- [ ] Tool result caching
