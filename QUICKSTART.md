# Quick Start Guide

Get up and running with AI Chat in minutes!

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Google Cloud account with Vertex AI enabled
- (Optional) MCP servers running

## 1. Install

```bash
# Clone repository
git clone https://github.com/sirimamilla/ai-chat.git
cd ai-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

Minimum required configuration in `.env`:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_chat
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
```

## 3. Set Up Google Cloud Authentication

```bash
# Option 1: Use gcloud CLI
gcloud auth application-default login

# Option 2: Use service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## 4. Initialize Database

```bash
# Create PostgreSQL database
createdb ai_chat

# Initialize schema
python main.py init-database
```

## 5. Run!

### Option A: Interactive CLI

```bash
python main.py chat
```

### Option B: API Server

```bash
python main.py serve
```

Then test with:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user_id": "test-user"}'
```

### Option C: Docker Compose

```bash
# Set up environment
echo "GOOGLE_CLOUD_PROJECT=your-project-id" > .env
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json" >> .env

# Start services
docker-compose up
```

## Example Usage

### CLI Chat
```bash
$ python main.py chat --user-id alice

AI Chat - Interactive Session
====================================
User ID: alice
Session ID: 123e4567-e89b-12d3-a456-426614174000
Type 'quit' or 'exit' to end the session
====================================

You: Hello!
Assistant: Hello! How can I help you today?

You: quit
Goodbye!
```

### API Chat
```python
import requests

# Create session
response = requests.post(
    "http://localhost:8000/session",
    json={"user_id": "alice"}
)
session_id = response.json()["session_id"]

# Send message
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "Hello!",
        "user_id": "alice",
        "session_id": session_id
    }
)
print(response.json()["response"])
```

## Configuration Tips

### Enable LangSmith Tracing (Optional)
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-api-key
LANGCHAIN_PROJECT=ai-chat
```

### Configure MCP Servers
Edit `config/mcp_servers.yaml`:
```yaml
servers:
  - name: my_tool
    description: "My custom tool"
    sse_endpoint: "http://localhost:3000/sse"
    enabled: true
    capabilities:
      - capability1
      - capability2
```

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -h localhost -U postgres -d ai_chat
```

### Vertex AI Authentication Error
```bash
# Verify authentication
gcloud auth application-default print-access-token

# Check project
gcloud config get-value project
```

### MCP Connection Error
- Ensure MCP servers are running
- Check SSE endpoints are accessible
- Verify `config/mcp_servers.yaml` is correct

## Next Steps

- Read the full [README](README.md) for detailed documentation
- Check [examples/](examples/) for more usage patterns
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Configure additional MCP servers in `config/mcp_servers.yaml`

## Support

- Issues: https://github.com/sirimamilla/ai-chat/issues
- Documentation: See README.md
