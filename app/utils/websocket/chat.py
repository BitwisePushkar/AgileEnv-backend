import asyncio
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

PING_INTERVAL = 25

class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[int, Dict[int, List[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, chatroom_id: int) -> None:
        await websocket.accept()
        user_rooms = self._connections.setdefault(user_id, {})
        sockets = user_rooms.setdefault(chatroom_id, [])
        sockets.append(websocket)
        logger.info("WS connected  user=%s room=%s connections=%s", user_id, chatroom_id, len(sockets))

    def disconnect(self, websocket: WebSocket, user_id: int, chatroom_id: int) -> None:
        try:
            sockets = self._connections[user_id][chatroom_id]
        except KeyError:
            return
        try:
            sockets.remove(websocket)
        except ValueError:
            pass
        if not sockets:
            del self._connections[user_id][chatroom_id]
        if not self._connections.get(user_id):
            self._connections.pop(user_id, None)
        logger.info("WS disconnected user=%s room=%s", user_id, chatroom_id)

    def is_online(self, user_id: int, chatroom_id: Optional[int] = None) -> bool:
        if user_id not in self._connections:
            return False
        if chatroom_id is None:
            return bool(self._connections[user_id])
        return bool(self._connections[user_id].get(chatroom_id))

    def get_online_user_ids(self, chatroom_id: int) -> Set[int]:
        return {uid for uid, rooms in self._connections.items() if chatroom_id in rooms and rooms[chatroom_id]}

    async def broadcast(self,chatroom_id: int,message: dict,member_ids: List[int],exclude_user: Optional[int] = None,) -> None:
        for user_id in member_ids:
            if exclude_user is not None and user_id == exclude_user:
                continue
            await self._send_to_user(message, user_id, chatroom_id)

    async def send_to_user(self, message: dict, user_id: int, chatroom_id: int) -> None:
        await self._send_to_user(message, user_id, chatroom_id)

    async def _send_to_user(self, message: dict, user_id: int, chatroom_id: int) -> None:
        try:
            sockets = self._connections[user_id][chatroom_id]
        except KeyError:
            return
        dead: List[WebSocket] = []
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.warning("Dead socket for user=%s room=%s: %s", user_id, chatroom_id, exc)
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, user_id, chatroom_id)

    async def _heartbeat(self, websocket: WebSocket, user_id: int, chatroom_id: int) -> None:
        try:
            while True:
                await asyncio.sleep(PING_INTERVAL)
                if not self.is_online(user_id, chatroom_id):
                    break
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    self.disconnect(websocket, user_id, chatroom_id)
                    break
        except asyncio.CancelledError:
            pass

manager = ConnectionManager()