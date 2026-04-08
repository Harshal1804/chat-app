from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), unique=True, index=True, nullable=False)
    email         = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
    messages      = relationship("Message", back_populates="user")

class Room(Base):
    __tablename__ = "rooms"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(200), default="")
    created_at  = Column(DateTime, default=datetime.utcnow)
    messages    = relationship("Message", back_populates="room")

class Message(Base):
    __tablename__ = "messages"
    id         = Column(Integer, primary_key=True, index=True)
    content    = Column(Text, nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id    = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user       = relationship("User", back_populates="messages")
    room       = relationship("Room", back_populates="messages")
