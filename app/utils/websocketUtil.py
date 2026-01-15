from fastapi import WebSocket
from typing import Dict
from sqlalchemy.orm import Session
from app.chat.models import Chatroom

class ConnectionManager:

    def __init__(self):
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
    
    async def connect(self,websocket:WebSocket,user_id:int,chatroom_id:int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        self.active_connections[user_id][chatroom_id] = websocket
        print(f"User {user_id} connected to chatroom {chatroom_id}")
    
    def disconnect(self,user_id:int,chatroom_id:int):
        if user_id in self.active_connections:
            if chatroom_id in self.active_connections[user_id]:
                del self.active_connections[user_id][chatroom_id]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"User {user_id} disconnected from chatroom {chatroom_id}")
    
    async def send_to_user(self,message:dict,user_id:int,chatroom_id:int):
        if user_id in self.active_connections:
            if chatroom_id in self.active_connections[user_id]:
                try:
                    await self.active_connections[user_id][chatroom_id].send_json(message)
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    self.disconnect(user_id, chatroom_id)
    
    async def broadcast_to_chatroom(self,chatroom_id:int,message:dict,db:Session,exclude_user:int=None):
        chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
        if not chatroom:
            print(f"Chatroom {chatroom_id} not found")
            return
        member_ids = [member.id for member in chatroom.members]
        for user_id in member_ids:
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(message, user_id, chatroom_id)

manager = ConnectionManager()