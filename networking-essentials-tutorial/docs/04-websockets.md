# Module 4: WebSockets

## Why HTTP Isn't Enough

HTTP has a fundamental limitation:

```
Client initiates
  ↓
Server responds
  ↓
Connection closes
```

What if the server wants to send data to the client without the client asking?

### Real-World Scenarios

**Chat application**: Server receives message from user B, needs to send it to user A's browser immediately.

**Stock trading**: Price changes, server needs to push updates to all connected clients.

**Real-time notifications**: Event happens, server needs to alert user immediately.

**Live collaboration**: User A edits document, server needs to update all other users viewing that document.

With HTTP alone, you're stuck with:

1. **Polling**: Client asks "any updates?" every second
2. **Long polling**: Client asks, server holds response until data arrives
3. **Server-Sent Events**: Server can push, but one-way only

All are inefficient. HTTP requires client to initiate.

## WebSocket: A Better Way

WebSocket is a protocol that allows **bidirectional communication** over a single TCP connection.

### The Handshake

```
Client                          Server
  |                               |
  | -- HTTP Upgrade request ----> |
  |     GET /ws HTTP/1.1          |
  |     Upgrade: websocket        |
  |     Connection: Upgrade       |
  |                               |
  | <-- HTTP 101 response ------- |
  |     Switching Protocols       |
  |                               |
  | [WebSocket connection now open]
  |                               |
  | <-> (bidirectional) <-------> |
  |     Binary or text frames     |
  |                               |
```

### Key Differences from HTTP

| Aspect | HTTP | WebSocket |
|--------|------|-----------|
| Connection | Client initiates, response sent, closes | One connection, stays open |
| Direction | Request → Response | Bidirectional |
| Initiation | Client asks | Either side can send |
| Overhead | High (headers with every request) | Low (minimal frame overhead) |
| Real-time | Slow (polling/long-poll) | Instant |
| Port | 80 (HTTP), 443 (HTTPS) | 80/443 (same, upgrades) |

## WebSocket vs Alternatives

### WebSocket vs Polling

**Polling:**
```
Client: "Any updates?"  → Server
Server: "No updates"    ← Client
Client: "Any updates?"  → Server (after 1 second)
Server: "No updates"    ← Client
Client: "Any updates?"  → Server (after 1 second)
Server: "New message from Alice"  ← Client

Wasteful: 99% of requests find nothing
```

**WebSocket:**
```
Client: Connect → Server
Server: Listening
(no overhead)
...
Server: New message from Alice → Client

Efficient: Only real data transmitted
```

### WebSocket vs Server-Sent Events (SSE)

**Server-Sent Events:**
```
Client connects → Server
Server can push updates to client
Client cannot send data to server

Use: One-way notifications (stock prices, news feeds)
```

**WebSocket:**
```
Client connects → Server
Both can send and receive anytime

Use: Chat, collaborative editing, real-time games
```

### WebSocket vs Long Polling

**Long Polling:**
```
Client: "Any updates? Wait for me..." → Server
Server: Holding connection...
(after 30 seconds or when data arrives)
Server: Response                 ← Client
Client: "Any updates? Wait for me..." → Server (reconnects)
Server: Holding...
(repeat)

Wasteful: Constant reconnects
```

**WebSocket:**
```
Client: Connect → Server
(Single connection stays open)
Server: Updates whenever         ← Client
Client: Responds if needed       → Server

Efficient: One connection forever
```

## Building a WebSocket Backend

### Flask + Flask-SocketIO (Recommended for Flask)

```bash
pip install flask-socketio python-socketio
```

Basic server:

```python
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Handle client connecting
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('response', {'data': 'Connected to server'})

# Handle custom message from client
@socketio.on('message')
def handle_message(data):
    print(f'Received: {data}')
    # Send to all connected clients
    emit('message', {'data': data}, broadcast=True)

# Handle client disconnecting
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

Client (JavaScript):

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>WebSocket Chat</h1>
    <input type="text" id="message" placeholder="Type message">
    <button onclick="sendMessage()">Send</button>
    <div id="messages"></div>

    <script>
        const socket = io();

        socket.on('connect', function() {
            console.log('Connected to server');
        });

        socket.on('message', function(data) {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML += `<p>${data.data}</p>`;
        });

        function sendMessage() {
            const input = document.getElementById('message');
            socket.emit('message', input.value);
            input.value = '';
        }

        socket.on('disconnect', function() {
            console.log('Disconnected from server');
        });
    </script>
</body>
</html>
```

### FastAPI + WebSockets

```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            print(f"Received: {data}")
            
            # Send back (echo server)
            await websocket.send_text(f"Server received: {data}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
```

Client:

```python
import asyncio
import websockets

async def main():
    async with websockets.connect('ws://localhost:8000/ws') as websocket:
        # Send message
        await websocket.send("Hello server")
        
        # Receive message
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(main())
```

## Real-Time Chat Example

### Server (Flask-SocketIO)

```python
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

users = {}  # Store connected users

@socketio.on('connect')
def on_connect():
    print(f'User {id} connected')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    
    users[request.sid] = {'username': username, 'room': room}
    
    join_room(room)
    
    # Notify others in room
    emit('message', {
        'username': 'System',
        'message': f'{username} joined the chat'
    }, room=room)

@socketio.on('send_message')
def on_message(data):
    room = users[request.sid]['room']
    username = users[request.sid]['username']
    message = data['message']
    
    # Broadcast to all in room
    emit('message', {
        'username': username,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, room=room)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in users:
        user = users[request.sid]
        room = user['room']
        username = user['username']
        
        del users[request.sid]
        
        leave_room(room)
        
        emit('message', {
            'username': 'System',
            'message': f'{username} left the chat'
        }, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

## Scaling WebSockets

Single server can handle ~10,000 WebSocket connections.

What if you need more?

### Problem: Multiple Servers

```
Load Balancer
  ↓
Server 1 (10,000 connections)
Server 2 (10,000 connections)
Server 3 (10,000 connections)

User A connected to Server 1
User B connected to Server 2

User A sends message to User B
Server 1 doesn't know how to reach User B
```

### Solution: Message Broker (Redis)

```
Server 1
  ↓ (publish message)
Redis (message broker)
  ↑ (subscribe)
Server 2 (receives message, sends to User B)
```

Flask-SocketIO with Redis:

```bash
pip install redis
```

```python
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Use Redis message queue for scaling
socketio = SocketIO(
    app,
    message_queue='redis://localhost:6379'
)

# Rest of code same as before
@socketio.on('message')
def handle_message(data):
    emit('message', {'data': data}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

### Architecture with Redis

```
Client A ---+
            |
        [Nginx Load Balancer]
            |
Client B ---+-- Server 1 ----+
                              |
                            Redis
                              |
Client C ---+-- Server 2 ----+
            |
        [Nginx Load Balancer]
            |
Client D ---+
```

All servers publish/subscribe through Redis. Messages reach all clients regardless of which server they connected to.

## Common WebSocket Patterns

### Pattern 1: Rooms (Multi-user Spaces)

```python
@socketio.on('join_room')
def on_join_room(data):
    room = data['room_id']
    join_room(room)
    emit('message', {'text': 'User joined'}, room=room)

@socketio.on('send_to_room')
def on_send_to_room(data):
    room = data['room_id']
    message = data['message']
    emit('message', {'text': message}, room=room)
```

### Pattern 2: Direct Messages

```python
@socketio.on('direct_message')
def on_direct_message(data):
    recipient_id = data['recipient_id']
    message = data['message']
    
    # Send only to specific user
    emit('message', 
         {'from': request.sid, 'text': message},
         to=recipient_id)
```

### Pattern 3: Broadcasting to All

```python
@socketio.on('broadcast_message')
def on_broadcast(data):
    message = data['message']
    
    # Send to all connected users
    emit('message', {'text': message}, broadcast=True)
```

### Pattern 4: Presence Awareness

```python
active_users = set()

@socketio.on('connect')
def on_connect():
    active_users.add(request.sid)
    emit('users_online', {'count': len(active_users)}, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    active_users.discard(request.sid)
    emit('users_online', {'count': len(active_users)}, broadcast=True)
```

## Common Mistakes

### Mistake 1: Not Handling Reconnections

Clients disconnect (network drop, browser tab closed, etc.). Handle gracefully:

```python
@socketio.on('connect')
def on_connect():
    # Send client their previous state
    previous_messages = db.query(Message).limit(50).all()
    emit('sync', {
        'messages': [m.to_dict() for m in previous_messages]
    })

@socketio.on('disconnect')
def on_disconnect():
    # Clean up, but don't immediately delete user data
    # They might reconnect soon
    mark_user_as_offline(request.sid)
```

### Mistake 2: Missing Heartbeat

If no data is sent for ~30 seconds, proxies close the connection:

```python
# Flask-SocketIO handles heartbeat automatically
# But verify your proxy doesn't close idle connections

# In Nginx:
location /socket.io {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_read_timeout 3600;  # Keep connection open
}
```

### Mistake 3: Not Validating Messages

```python
# Wrong: Trust everything from client
@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

# Right: Validate and sanitize
@socketio.on('message')
def handle_message(data):
    if not isinstance(data, dict):
        return
    
    message = data.get('message', '')
    if not isinstance(message, str):
        return
    
    if len(message) > 1000:
        emit('error', {'text': 'Message too long'})
        return
    
    # Sanitize (remove HTML/JS)
    safe_message = escape_html(message)
    
    emit('message', {'text': safe_message}, broadcast=True)
```

### Mistake 4: Memory Leaks from Unhandled Errors

```python
# Wrong: No error handling
@socketio.on('message')
def handle_message(data):
    process_message(data)
    emit('message', data, broadcast=True)

# Right: Handle errors
@socketio.on('message')
def handle_message(data):
    try:
        process_message(data)
        emit('message', data, broadcast=True)
    except Exception as e:
        print(f"Error: {e}")
        emit('error', {'text': 'Failed to process message'})
```

## Production Notes

### 1. Use Nginx to Handle WebSockets

```nginx
upstream websocket {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /socket.io {
        proxy_pass http://websocket;
        
        # Required for WebSocket upgrade
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        
        # Prevent timeout
        proxy_read_timeout 3600;
        proxy_send_timeout 3600;
        
        # Pass headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Monitor Connection Count

```python
from flask_socketio import SocketIO

socketio = SocketIO(app, message_queue='redis://localhost:6379')

@app.route('/metrics')
def metrics():
    # In production, use prometheus client
    return {
        'connected_clients': len(socketio.server.environ),
        'active_rooms': len(socketio.server.rooms)
    }
```

### 3. Graceful Shutdown

```python
import signal
import sys

def shutdown_handler(sig, frame):
    print("Shutting down gracefully...")
    # Disconnect all clients with message
    socketio.emit('server_shutting_down', 
                  {'message': 'Server is restarting'},
                  broadcast=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

### 4. Rate Limiting per Connection

```python
from functools import wraps
from time import time

def rate_limit(max_calls, time_window):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = request.sid
            key = f"{user_id}:{f.__name__}"
            
            # Check if user exceeded limit
            calls = cache.get(key, [])
            now = time()
            
            # Remove old calls outside time window
            calls = [c for c in calls if now - c < time_window]
            
            if len(calls) >= max_calls:
                emit('error', {'text': 'Rate limit exceeded'})
                return
            
            calls.append(now)
            cache.set(key, calls)
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

@socketio.on('send_message')
@rate_limit(max_calls=10, time_window=60)  # Max 10 messages per minute
def handle_message(data):
    emit('message', data, broadcast=True)
```

---

## Module 4 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. Why is HTTP insufficient for real-time chat applications?
   a) HTTP is too slow
   b) HTTP can't handle text data
   c) HTTP requires client to initiate, not server
   d) HTTP connections are expensive

2. WebSocket upgrade happens using:
   a) TCP SYN packet
   b) HTTP Upgrade header
   c) Special WebSocket port
   d) TLS handshake

3. Compared to polling every 1 second, WebSocket is more efficient because:
   a) WebSocket is faster
   b) WebSocket is encrypted
   c) WebSocket reuses connection, doesn't create new requests constantly
   d) WebSocket always sends less data

4. When scaling WebSockets across multiple servers, which is necessary?
   a) Sticky sessions (always route client to same server)
   b) Message broker like Redis for cross-server communication
   c) Load balancer for distributing connections
   d) All of the above

5. A WebSocket connection drops after 30 seconds of idle time. Most likely cause?
   a) Server closed it
   b) Client closed it
   c) Proxy/firewall closed it due to timeout
   d) Network interface reset

### Practical Networking Tasks

**Task 1: Build Simple WebSocket Chat**

- Create a Flask-SocketIO server with chat functionality
- Create HTML client that:
  - Connects to server
  - Sends messages
  - Receives messages from others
  - Shows list of connected users
- Test with multiple browser tabs/windows
- Verify that messages broadcast to all connected clients

**Task 2: Monitor WebSocket Connections**

- Start your WebSocket server
- Connect multiple clients
- Monitor connections using:
  ```bash
  netstat -an | grep :5000
  # or
  ss -tan | grep :5000
  ```
- Disconnect clients and verify connections close
- Use `ps aux | grep python` to see which processes have open connections

### Production Incident Scenario

**Incident**: Your real-time chat application works fine with 100 users on one server. When you scale to 3 servers behind a load balancer, messages stop reaching users on different servers.

```
Server 1: User A connected
Server 2: User B connected

User A sends message to User B
Server 1 knows User A, broadcasts to connected clients
User B doesn't receive message (on different server)
```

Questions:

1. Why isn't User B receiving messages from User A?
2. What's missing in your scaling architecture?
3. How would you fix this?
4. What infrastructure component would you add?
5. How do you ensure messages reach all connected clients?

---

**Next**: [Module 5: Load Balancing](05-load-balancing.md)
