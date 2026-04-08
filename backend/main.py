from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime

from database import get_db, engine
from models import Base, User, Message, Room
from auth import hash_password, verify_password, create_token, verify_token
from schemas import UserRegister, UserLogin, RoomCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RealTime Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket Connection Manager ────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        # room_id -> list of (websocket, user_info)
        self.rooms: Dict[int, List[dict]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user: dict):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append({"ws": websocket, "user": user})
        await self.broadcast_presence(room_id)

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.rooms:
            self.rooms[room_id] = [c for c in self.rooms[room_id] if c["ws"] != websocket]
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: int, message: dict, exclude: WebSocket = None):
        if room_id not in self.rooms:
            return
        dead = []
        for conn in self.rooms[room_id]:
            if conn["ws"] == exclude:
                continue
            try:
                await conn["ws"].send_text(json.dumps(message))
            except:
                dead.append(conn)
        for d in dead:
            self.rooms[room_id].remove(d)

    async def broadcast_presence(self, room_id: int):
        if room_id not in self.rooms:
            return
        users = [c["user"]["username"] for c in self.rooms[room_id]]
        await self.broadcast(room_id, {
            "type": "presence",
            "online_users": users,
            "count": len(users)
        })

    async def send_to(self, websocket: WebSocket, message: dict):
        await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

# ─── HTTP Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("/app/frontend/index.html")

@app.post("/api/register")
async def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"user_id": user.id, "username": user.username})
    return {"token": token, "username": user.username, "user_id": user.id}

@app.post("/api/login")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"user_id": user.id, "username": user.username})
    return {"token": token, "username": user.username, "user_id": user.id}

@app.get("/api/rooms")
async def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    return [{"id": r.id, "name": r.name, "description": r.description} for r in rooms]

@app.post("/api/rooms")
async def create_room(data: RoomCreate, token: str, db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    if db.query(Room).filter(Room.name == data.name).first():
        raise HTTPException(status_code=400, detail="Room already exists")
    room = Room(name=data.name, description=data.description)
    db.add(room)
    db.commit()
    db.refresh(room)
    return {"id": room.id, "name": room.name, "description": room.description}

@app.get("/api/rooms/{room_id}/messages")
async def get_messages(room_id: int, limit: int = 50, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "content": m.content,
            "username": m.user.username,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(messages)
    ]

# ─── WebSocket Route ──────────────────────────────────────────────────────────

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str, db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        await websocket.close(code=4004)
        return

    user_info = {"user_id": payload["user_id"], "username": payload["username"]}
    await manager.connect(websocket, room_id, user_info)

    # Send join notification
    await manager.broadcast(room_id, {
        "type": "system",
        "content": f"{user_info['username']} joined the room",
        "timestamp": datetime.utcnow().isoformat()
    }, exclude=websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                content = data.get("content", "").strip()
                if not content or len(content) > 1000:
                    continue

                # Persist message
                msg = Message(
                    content=content,
                    user_id=payload["user_id"],
                    room_id=room_id
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                # Broadcast to all in room
                await manager.broadcast(room_id, {
                    "type": "message",
                    "id": msg.id,
                    "content": content,
                    "username": user_info["username"],
                    "user_id": payload["user_id"],
                    "timestamp": msg.created_at.isoformat()
                })

            elif data.get("type") == "typing":
                await manager.broadcast(room_id, {
                    "type": "typing",
                    "username": user_info["username"],
                    "is_typing": data.get("is_typing", False)
                }, exclude=websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(room_id, {
            "type": "system",
            "content": f"{user_info['username']} left the room",
            "timestamp": datetime.utcnow().isoformat()
        })
        await manager.broadcast_presence(room_id)
    except Exception as e:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_presence(room_id)
