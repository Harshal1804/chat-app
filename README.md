# ⬡ DockChat — Containerized Real-Time Chat App

A real-time chat application built with **Python FastAPI + WebSockets**, containerized using **Docker Desktop**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Docker Desktop                │
│                                         │
│  ┌──────────────────┐  ┌─────────────┐ │
│  │  docchat_app     │  |  docchat_db │ │
│  │                  │  │             │ │
│  │  Python 3.11     │◄─►  PostgreSQL │ │
│  │  FastAPI         │  │     16      │ │
│  │  WebSockets      │  │             │ │
│  │  PORT: 8000      │  │  PORT: 5432 │ │
│  └──────────────────┘  └─────────────┘ │
│           │                             │
│     chat_net (bridge)                   │
└───────────┼─────────────────────────────┘
            │
     http://localhost:8000
```

## 📁 Project Structure

```
chat-app/
├── docker-compose.yml       ← Orchestrates both containers
├── .dockerignore
├── backend/
│   ├── Dockerfile           ← Builds the app container
│   ├── requirements.txt
│   ├── main.py              ← FastAPI app + WebSocket logic
│   ├── models.py            ← SQLAlchemy DB models
│   ├── database.py          ← DB connection
│   ├── auth.py              ← JWT + bcrypt auth
│   ├── schemas.py           ← Pydantic request schemas
│   └── seed.py              ← Creates default rooms on startup
└── frontend/
    └── index.html           ← Single-page chat UI
```

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Run the app


# 1. Clone / download this project folder
cd chat-app

# 2. Build and start both containers
docker-compose up --build

# 3. Open your browser
open http://localhost:8000
```

That's it! Both containers will start automatically.

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Authentication | Register & login with JWT tokens |
| 💬 Real-time chat | WebSockets for instant messaging |
| 🏠 Multiple rooms | #general, #tech-talk, #random + create your own |
| 👥 Online presence | See who's in the room live |
| ✍️ Typing indicator | See when others are typing |
| 💾 Message history | PostgreSQL stores all messages |

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register` | Create a new account |
| POST | `/api/login` | Sign in |
| GET | `/api/rooms` | List all rooms |
| POST | `/api/rooms?token=...` | Create a new room |
| GET | `/api/rooms/{id}/messages` | Fetch message history |
| WS | `/ws/{room_id}?token=...` | WebSocket connection |

## 🔧 Useful Docker Commands

```bash
# Start in background
docker-compose up -d --build

# View live logs
docker-compose logs -f

# View logs for just the app
docker-compose logs -f app

# Stop everything
docker-compose down

# Stop and delete database data
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

## 🔌 WebSocket Message Protocol

**Client → Server:**
```json
{ "type": "message", "content": "Hello!" }
{ "type": "typing", "is_typing": true }
```

**Server → Client:**
```json
{ "type": "message", "username": "alice", "content": "Hello!", "timestamp": "..." }
{ "type": "system", "content": "bob joined the room" }
{ "type": "presence", "online_users": ["alice", "bob"], "count": 2 }
{ "type": "typing", "username": "alice", "is_typing": true }
```

## 🎓 Key Concepts Demonstrated

1. **Docker multi-container app** using `docker-compose`
2. **Container networking** — app talks to DB via service name `db`
3. **Health checks** — app waits for DB to be ready before starting
4. **Persistent volumes** — DB data survives container restarts
5. **WebSockets** — bidirectional real-time communication
6. **JWT authentication** — stateless token-based auth
7. **REST + WebSocket hybrid API**

## 🔒 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://chatuser:chatpass@db:5432/chatdb` | PostgreSQL connection string |
| `SECRET_KEY` | `change-this-secret-in-production-please` | JWT signing secret |

> ⚠️ Change `SECRET_KEY` for any real deployment!
