from fastapi import WebSocket
from typing import Dict, List
from sqlalchemy.orm import Session
from app.chat.models import Chatroom
from app.utils.dbUtil import SessionLocal

class ConnectionManager:

    def __init__(self):
        self.active_connections: Dict[int, Dict[int, List[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, chatroom_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        if chatroom_id not in self.active_connections[user_id]:
            self.active_connections[user_id][chatroom_id] = []
        self.active_connections[user_id][chatroom_id].append(websocket)
        print(f"User {user_id} connected to chatroom {chatroom_id} "
              f"({len(self.active_connections[user_id][chatroom_id])} connection(s))")

    def disconnect(self, user_id: int, chatroom_id: int, websocket: WebSocket = None):
        if user_id not in self.active_connections:
            return
        if chatroom_id not in self.active_connections[user_id]:
            return
        if websocket is not None:
            try:
                self.active_connections[user_id][chatroom_id].remove(websocket)
            except ValueError:
                pass
        else:
            self.active_connections[user_id][chatroom_id] = []
        if not self.active_connections[user_id][chatroom_id]:
            del self.active_connections[user_id][chatroom_id]
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
        print(f"User {user_id} disconnected from chatroom {chatroom_id}")

    async def send_to_user(self, message: dict, user_id: int, chatroom_id: int):
        if user_id not in self.active_connections:
            return
        if chatroom_id not in self.active_connections[user_id]:
            return
        dead: List[WebSocket] = []
        for ws in self.active_connections[user_id][chatroom_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"Error sending to user {user_id} (tab): {e}")
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, chatroom_id, websocket=ws)

    async def broadcast_to_chatroom(self,chatroom_id: int,message: dict,db: Session = None,      
                                    exclude_user: int = None,):
        fresh_db = SessionLocal()
        try:
            chatroom = fresh_db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
            if not chatroom:
                print(f"Chatroom {chatroom_id} not found for broadcast")
                return
            member_ids = [member.id for member in chatroom.members]
        except Exception as e:
            print(f"Broadcast DB error for chatroom {chatroom_id}: {e}")
            return
        finally:
            fresh_db.close()
        for user_id in member_ids:
            if exclude_user and user_id == exclude_user:
                continue
            await self.send_to_user(message, user_id, chatroom_id)

manager = ConnectionManager()