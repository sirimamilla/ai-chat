# AI Chat

An agentic AI chat tool that integrates with Vertex AI and uses PostgreSQL as the RAG database. It integrates with remote tools using MCP (Model Context Protocol) SSE endpoints.

## Features

- **Vertex AI Integration**: Uses Google Vertex AI Gemini models for powerful language understanding
- **PostgreSQL RAG Database**: Stores conversation history and documents for retrieval-augmented generation
- **MCP Tool Integration**: Connects to remote tools via MCP SSE endpoints
- **Dynamic Tool Selection**: Automatically selects relevant tools based on user requests
- **Multi-User Support**: Handles multiple concurrent users with session management
- **Multi-Instance Deployment**: Designed for horizontal scaling with database-backed state
- **Chat Memory**: Persistent conversation history stored in PostgreSQL
- **Configurable MCP Servers**: Easy configuration of multiple MCP servers

## Architecture

The application is built using:
- **Python**: Core language
- **LangChain**: LLM framework and tool orchestration
- **LangGraph**: Agentic workflow orchestration
- **LangSmith**: Optional observability and monitoring
- **PostgreSQL**: Database for chat history and RAG
- **FastAPI**: REST API server
- **Vertex AI**: Google's Gemini models

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Google Cloud project with Vertex AI API enabled
- MCP servers running with SSE endpoints (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sirimamilla/ai-chat.git
cd ai-chat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Configure MCP servers:
```bash
# Edit config/mcp_servers.yaml to configure your MCP servers
```

5. Initialize the database:
```bash
python main.py init-database
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.0-flash-exp

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_chat
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# LangSmith Configuration (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=ai-chat

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### MCP Server Configuration

Edit `config/mcp_servers.yaml` to configure your MCP servers:

```yaml
servers:
  - name: filesystem
    description: "Access and manipulate files and directories"
    sse_endpoint: "http://localhost:3000/sse"
    enabled: true
    capabilities:
      - read_file
      - write_file
      - list_directory

tool_selection:
  keywords:
    filesystem:
      - file
      - directory
      - folder
  default_tools:
    - filesystem
  max_tools: 5
```

## Usage

### Command-Line Interface

Start an interactive chat session:
```bash
python main.py chat --user-id "user123"
```

### API Server

Start the FastAPI server:
```bash
python main.py serve
```

Or with custom host/port:
```bash
python main.py serve --host 0.0.0.0 --port 8000
```

### API Endpoints

#### POST /chat
Send a message to the chat agent:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me with files?",
    "user_id": "user123",
    "session_id": "optional-session-id"
  }'
```

#### POST /session
Create a new session:
```bash
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123"
  }'
```

#### POST /history
Get chat history:
```bash
curl -X POST http://localhost:8000/history \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "user_id": "user123",
    "limit": 10
  }'
```

#### GET /health
Health check:
```bash
curl http://localhost:8000/health
```

### Using with Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "serve"]
```

Build and run:
```bash
docker build -t ai-chat .
docker run -p 8000:8000 --env-file .env ai-chat
```

## Multi-Instance Deployment

The application is designed for horizontal scaling:

1. **Database-Backed State**: All session and conversation data is stored in PostgreSQL
2. **Stateless API**: Each API instance can handle any request
3. **Connection Pooling**: PostgreSQL connection pooling ensures efficient database usage
4. **Session Isolation**: Each user session is independent and can be handled by any instance

Deploy multiple instances behind a load balancer:
```bash
# Instance 1
python main.py serve --port 8001

# Instance 2
python main.py serve --port 8002

# Instance 3
python main.py serve --port 8003
```

## Dynamic Tool Selection

The application automatically selects appropriate tools based on user requests:

1. **Keyword Matching**: Analyzes user input for keywords associated with each tool
2. **Default Tools**: Always includes configured default tools
3. **Configurable Limits**: Respects maximum tool count to avoid overwhelming the model
4. **Force Override**: API can force specific tools to be loaded

Example:
```python
# User says: "Can you read the config file?"
# System automatically loads: filesystem tools

# User says: "Search for information about Python"
# System automatically loads: web_search tools
```

## Development

### Project Structure

```
ai-chat/
├── config/
│   └── mcp_servers.yaml       # MCP server configuration
├── src/
│   └── ai_chat/
│       ├── __init__.py
│       ├── agent.py           # Main agent with LangGraph
│       ├── api.py             # FastAPI server
│       ├── cli.py             # Command-line interface
│       ├── config.py          # Configuration management
│       ├── database.py        # Database models and setup
│       ├── memory.py          # Chat memory implementation
│       ├── mcp_client.py      # MCP SSE client
│       └── tool_selector.py   # Dynamic tool selection
├── tests/                     # Tests
├── .env.example               # Environment variable template
├── .gitignore
├── main.py                    # Entry point
├── README.md
├── requirements.txt
└── setup.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_chat
```

### Code Quality

```bash
# Format code
black src/

# Lint code
pylint src/ai_chat

# Type checking
mypy src/ai_chat
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify connection details in `.env`
- Check firewall rules

### Vertex AI Authentication
- Ensure Google Cloud credentials are set up
- Run `gcloud auth application-default login`
- Verify project ID and location

### MCP Server Connection
- Ensure MCP servers are running
- Verify SSE endpoints are accessible
- Check `config/mcp_servers.yaml` configuration

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- GitHub Issues: https://github.com/sirimamilla/ai-chat/issues
