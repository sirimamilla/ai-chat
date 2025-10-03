# API Documentation

Complete REST API reference for AI Chat.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, authentication is handled via `user_id` in request bodies. Future versions will support JWT/OAuth.

## Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Root

Get API information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "AI Chat API",
  "version": "0.1.0",
  "status": "running"
}
```

---

### 3. Create Session

Create a new chat session for a user.

**Endpoint:** `POST /session`

**Request Body:**
```json
{
  "user_id": "string"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "user_id": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

**Response Example:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user123",
  "created_at": "2024-01-15T10:30:00.000000"
}
```

---

### 4. Chat

Send a message to the chat agent.

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "message": "string",
  "user_id": "string",
  "session_id": "string (optional)"
}
```

**Parameters:**
- `message` (required): The user's message
- `user_id` (required): User identifier
- `session_id` (optional): Session ID. If not provided, a new session will be created.

**Response:**
```json
{
  "response": "string",
  "session_id": "string",
  "user_id": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me?",
    "user_id": "user123",
    "session_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

**Response Example:**
```json
{
  "response": "Hello! Of course, I'd be happy to help. What do you need assistance with?",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user123"
}
```

---

### 5. Get History

Retrieve chat history for a session.

**Endpoint:** `POST /history`

**Request Body:**
```json
{
  "session_id": "string",
  "user_id": "string",
  "limit": "integer (optional, default: 10)"
}
```

**Response:**
```json
{
  "session_id": "string",
  "user_id": "string",
  "messages": [
    {
      "role": "string",
      "content": "string",
      "created_at": "string",
      "metadata": {}
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/history \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user123",
    "limit": 20
  }'
```

**Response Example:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user123",
  "messages": [
    {
      "role": "user",
      "content": "Hello!",
      "created_at": "2024-01-15T10:30:00.000000",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help you?",
      "created_at": "2024-01-15T10:30:05.000000",
      "metadata": {}
    }
  ]
}
```

---

### 6. Delete Session

Mark a session as inactive.

**Endpoint:** `DELETE /session/{session_id}`

**Query Parameters:**
- `user_id` (required): User identifier

**Example:**
```bash
curl -X DELETE "http://localhost:8000/session/123e4567-e89b-12d3-a456-426614174000?user_id=user123"
```

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Tool selector not initialized"
}
```

---

## Usage Patterns

### Pattern 1: New Conversation

```bash
# 1. Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice"}' | jq -r '.session_id')

# 2. Send messages
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Hello!\",
    \"user_id\": \"alice\",
    \"session_id\": \"$SESSION_ID\"
  }"

# 3. Continue conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Can you read a file?\",
    \"user_id\": \"alice\",
    \"session_id\": \"$SESSION_ID\"
  }"
```

### Pattern 2: Resume Conversation

```bash
# If you have a session_id, just continue
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Continue from where we left off",
    "user_id": "alice",
    "session_id": "existing-session-id"
  }'
```

### Pattern 3: Auto-Session Creation

```bash
# Don't provide session_id, one will be created automatically
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quick question!",
    "user_id": "alice"
  }'
```

---

## Client Examples

### Python

```python
import requests

class ChatClient:
    def __init__(self, base_url="http://localhost:8000", user_id="user"):
        self.base_url = base_url
        self.user_id = user_id
        self.session_id = None

    def create_session(self):
        response = requests.post(
            f"{self.base_url}/session",
            json={"user_id": self.user_id}
        )
        self.session_id = response.json()["session_id"]
        return self.session_id

    def chat(self, message):
        if not self.session_id:
            self.create_session()

        response = requests.post(
            f"{self.base_url}/chat",
            json={
                "message": message,
                "user_id": self.user_id,
                "session_id": self.session_id
            }
        )
        return response.json()["response"]

    def get_history(self, limit=10):
        response = requests.post(
            f"{self.base_url}/history",
            json={
                "session_id": self.session_id,
                "user_id": self.user_id,
                "limit": limit
            }
        )
        return response.json()["messages"]

# Usage
client = ChatClient(user_id="alice")
response = client.chat("Hello!")
print(response)
```

### JavaScript

```javascript
class ChatClient {
  constructor(baseUrl = "http://localhost:8000", userId = "user") {
    this.baseUrl = baseUrl;
    this.userId = userId;
    this.sessionId = null;
  }

  async createSession() {
    const response = await fetch(`${this.baseUrl}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.userId })
    });
    const data = await response.json();
    this.sessionId = data.session_id;
    return this.sessionId;
  }

  async chat(message) {
    if (!this.sessionId) {
      await this.createSession();
    }

    const response = await fetch(`${this.baseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        user_id: this.userId,
        session_id: this.sessionId
      })
    });
    const data = await response.json();
    return data.response;
  }

  async getHistory(limit = 10) {
    const response = await fetch(`${this.baseUrl}/history`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: this.sessionId,
        user_id: this.userId,
        limit: limit
      })
    });
    const data = await response.json();
    return data.messages;
  }
}

// Usage
const client = new ChatClient("http://localhost:8000", "alice");
const response = await client.chat("Hello!");
console.log(response);
```

### cURL Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
USER_ID="alice"

# Create session
echo "Creating session..."
SESSION_ID=$(curl -s -X POST $BASE_URL/session \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\"}" | jq -r '.session_id')

echo "Session ID: $SESSION_ID"

# Chat function
chat() {
    local message=$1
    echo "You: $message"
    response=$(curl -s -X POST $BASE_URL/chat \
      -H "Content-Type: application/json" \
      -d "{
        \"message\": \"$message\",
        \"user_id\": \"$USER_ID\",
        \"session_id\": \"$SESSION_ID\"
      }" | jq -r '.response')
    echo "Assistant: $response"
    echo ""
}

# Example conversation
chat "Hello!"
chat "Can you help me with files?"
chat "Thank you!"
```

---

## Rate Limiting

Currently, there is no rate limiting. Consider implementing rate limiting in production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: ChatRequest):
    # ... implementation
```

---

## WebSocket Support (Future)

Future versions will support WebSocket for real-time streaming:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat");

ws.send(JSON.stringify({
  message: "Hello!",
  user_id: "alice",
  session_id: "session-id"
}));

ws.onmessage = (event) => {
  console.log("Received:", event.data);
};
```
