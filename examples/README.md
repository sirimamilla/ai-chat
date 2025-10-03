# AI Chat Examples

This directory contains example scripts and usage patterns for the AI Chat application.

## Examples

### example_usage.py

Demonstrates how to use AI Chat programmatically in Python:

```bash
python examples/example_usage.py
```

This example shows:
- Database initialization
- Tool selector setup
- Agent creation
- Sending messages
- Retrieving conversation history

## Creating Your Own Examples

Here's a minimal example to get started:

```python
import asyncio
from src.ai_chat.agent import ChatAgent
from src.ai_chat.database import init_db
from src.ai_chat.tool_selector import ToolSelector

async def chat_example():
    # Initialize
    init_db()
    tool_selector = ToolSelector.from_config_file()
    
    # Create agent
    agent = ChatAgent(
        session_id="my-session",
        user_id="my-user",
        tool_selector=tool_selector
    )
    
    # Chat
    response = await agent.chat("Hello!")
    print(response)
    
    # Cleanup
    agent.close()

asyncio.run(chat_example())
```

## API Usage Examples

### Using curl

```bash
# Create a session
SESSION_ID=$(curl -s -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}' | jq -r '.session_id')

# Send a message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Hello, how are you?\",
    \"user_id\": \"user123\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Get history
curl -X POST http://localhost:8000/history \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"user_id\": \"user123\",
    \"limit\": 10
  }"
```

### Using Python requests

```python
import requests

# Create session
response = requests.post(
    "http://localhost:8000/session",
    json={"user_id": "user123"}
)
session_id = response.json()["session_id"]

# Send message
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "Hello!",
        "user_id": "user123",
        "session_id": session_id
    }
)
print(response.json()["response"])
```

### Using JavaScript/TypeScript

```javascript
// Create session
const sessionResponse = await fetch('http://localhost:8000/session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 'user123' })
});
const { session_id } = await sessionResponse.json();

// Send message
const chatResponse = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello!',
    user_id: 'user123',
    session_id: session_id
  })
});
const { response } = await chatResponse.json();
console.log(response);
```
