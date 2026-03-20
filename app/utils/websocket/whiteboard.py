import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
import app.auth.models          
import app.workspace.model    
import app.project.model       
import app.kanban.models       
import app.scrum.model        
import app.chat.models          
import app.whiteboard.model   
from app.utils.dbUtil import SessionLocal
from app.utils import JWTUtil
from app.auth.models import User
from app.whiteboard import crud
from app.whiteboard import schemas
from app.utils.redis import whiteboard_redis
from app.project.crud import is_project_member
from app.whiteboard.model import ActionType

logger = logging.getLogger(__name__)
PING_INTERVAL = 25  

class WhiteboardConnectionManager:
    def __init__(self) -> None:
        self._rooms: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, ws: WebSocket, whiteboard_id: int, user_id: int) -> None:
        await ws.accept()
        self._rooms.setdefault(whiteboard_id, {})[user_id] = ws
        logger.info("WB-WS connect  board=%s user=%s", whiteboard_id, user_id)

    def disconnect(self, whiteboard_id: int, user_id: int) -> None:
        room = self._rooms.get(whiteboard_id, {})
        room.pop(user_id, None)
        if not room:
            self._rooms.pop(whiteboard_id, None)
        logger.info("WB-WS disconnect board=%s user=%s", whiteboard_id, user_id)

    def get_local_user_ids(self, whiteboard_id: int) -> Set[int]:
        return set(self._rooms.get(whiteboard_id, {}).keys())

    async def send_to_user(self, whiteboard_id: int, user_id: int, message: dict) -> None:
        ws = self._rooms.get(whiteboard_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.warning("Dead WB socket board=%s user=%s: %s", whiteboard_id, user_id, exc)
                self.disconnect(whiteboard_id, user_id)

    async def broadcast_local(self, whiteboard_id: int, message: dict, exclude_user: Optional[int] = None,) -> None:
        room = dict(self._rooms.get(whiteboard_id, {}))
        dead: List[int] = []
        for uid, ws in room.items():
            if exclude_user is not None and uid == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.warning("Dead WB socket board=%s user=%s: %s", whiteboard_id, uid, exc)
                dead.append(uid)
        for uid in dead:
            self.disconnect(whiteboard_id, uid)

wb_manager = WhiteboardConnectionManager()

async def whiteboard_ws_endpoint(websocket: WebSocket, whiteboard_id: int, token: str,) -> None:
    payload = JWTUtil.decode_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id: Optional[int] = payload.get("user_id")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    db: Session = SessionLocal()
    try:
        board = crud.get_whiteboard_by_id(db, whiteboard_id)
        if not board:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        if not is_project_member(db, board.project_id, user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        display_name = user.username or user.email
    finally:
        db.close()
    await wb_manager.connect(websocket, whiteboard_id, user_id)
    user_info = {"id": user_id, "username": display_name, "avatar_url": None}
    whiteboard_redis.set_user_present(whiteboard_id, user_id, user_info)
    await _send_init(websocket, whiteboard_id, user_id, user_info)
    whiteboard_redis.publish_event(whiteboard_id, schemas.WS_UserJoined(user=schemas.UserMini(
        id=user_id, username=display_name)).model_dump())
    ping_task = asyncio.create_task(_ping_loop(websocket, whiteboard_id, user_id))
    redis_task = asyncio.create_task(_redis_listener(websocket, whiteboard_id, user_id))
    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except ValueError:
                await wb_manager.send_to_user(whiteboard_id, user_id,schemas.WS_Error(
                    code="INVALID_JSON", message="Message must be valid JSON.").model_dump(),)
                continue
            await _handle_message(raw, whiteboard_id, user_id)
    except WebSocketDisconnect:
        logger.info("WB-WS client disconnect board=%s user=%s", whiteboard_id, user_id)
    except Exception as exc:
        logger.exception("WB-WS unhandled error board=%s user=%s: %s", whiteboard_id, user_id, exc)
    finally:
        ping_task.cancel()
        redis_task.cancel()
        wb_manager.disconnect(whiteboard_id, user_id)
        whiteboard_redis.remove_user_presence(whiteboard_id, user_id)
        whiteboard_redis.remove_cursor(whiteboard_id, user_id)
        whiteboard_redis.publish_event(whiteboard_id, schemas.WS_UserLeft(user_id=user_id).model_dump())

async def _handle_message(raw: dict, whiteboard_id: int, user_id: int) -> None:
    msg_type = raw.get("type")
    read_only = {"cursor_move", "ping"}
    if msg_type not in read_only:
        db = SessionLocal()
        try:
            board = crud.get_whiteboard_by_id(db, whiteboard_id)
            if not board:
                return
            if board.is_locked:
                from app.project.crud import get_project_role
                role = get_project_role(db, board.project_id, user_id)
                if role not in ("admin", "owner"):
                    await wb_manager.send_to_user(whiteboard_id, user_id,
                                                  schemas.WS_Error(code="BOARD_LOCKED", message="Whiteboard is locked.").model_dump(),)
                    return
        finally:
            db.close()
    try:
        if msg_type == "ping":
            whiteboard_redis.refresh_presence_ttl(whiteboard_id)
            await wb_manager.send_to_user(whiteboard_id, user_id, schemas.WS_Pong().model_dump())
        elif msg_type == "cursor_move":
            await _handle_cursor_move(raw, whiteboard_id, user_id)
        elif msg_type == "draw_start":
            await _handle_draw_start(raw, whiteboard_id, user_id)
        elif msg_type == "draw_delta":
            await _handle_draw_delta(raw, whiteboard_id, user_id)
        elif msg_type == "draw_end":
            await _handle_draw_end(raw, whiteboard_id, user_id)
        elif msg_type == "element_update":
            await _handle_element_update(raw, whiteboard_id, user_id)
        elif msg_type == "element_move":
            await _handle_element_move(raw, whiteboard_id, user_id)
        elif msg_type == "element_resize":
            await _handle_element_resize(raw, whiteboard_id, user_id)
        elif msg_type == "element_delete":
            await _handle_element_delete(raw, whiteboard_id, user_id)
        elif msg_type == "undo":
            await _handle_undo(whiteboard_id, user_id)
        else:
            await wb_manager.send_to_user(whiteboard_id, user_id,schemas.WS_Error(
                code="UNKNOWN_EVENT",message=f"Unknown message type: {msg_type!r}",).model_dump(),)
    except Exception as exc:
        logger.exception("WS handler error type=%s board=%s user=%s: %s", msg_type, whiteboard_id, user_id, exc,)
        await wb_manager.send_to_user(whiteboard_id, user_id,schemas.WS_Error(code="INTERNAL_ERROR", message="Server error.").model_dump(),)

async def _handle_cursor_move(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        x = float(raw["x"])
        y = float(raw["y"])
    except (KeyError, TypeError, ValueError):
        return 
    whiteboard_redis.update_cursor(whiteboard_id, user_id, x, y)
    whiteboard_redis.publish_event(whiteboard_id, schemas.WS_CursorBroadcast(user_id=user_id, x=x, y=y,).model_dump())

async def _handle_draw_start(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_DrawStart(**raw)
    except Exception as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                       schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    db = SessionLocal()
    try:
        element = crud.create_element(db, whiteboard_id=whiteboard_id, element_type=msg.element_type.value,
                                       data=msg.data, created_by=user_id, z_index=msg.z_index,)
        out = schemas.WS_ElementCreated(temp_id=msg.temp_id,element=schemas.WhiteboardElementOut.model_validate(element)).model_dump()
    except ValueError as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    except Exception as exc:
        logger.error("draw_start failed board=%s user=%s: %s", whiteboard_id, user_id, exc)
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="CREATE_FAILED", message="Failed to create element.").model_dump(),)
        return
    finally:
        db.close()
    await wb_manager.send_to_user(whiteboard_id, user_id, out)
    whiteboard_redis.publish_event(whiteboard_id, {**out, "_exclude_user": user_id})

async def _handle_draw_delta(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_DrawDelta(**raw)
    except Exception:
        return 
    whiteboard_redis.append_draw_delta(whiteboard_id, msg.temp_id, msg.points)
    whiteboard_redis.publish_event(whiteboard_id, schemas.WS_DrawDeltaBroadcast(user_id=user_id,temp_id=msg.temp_id,
                                                                                points=msg.points,)
                                                                                .model_dump())

async def _handle_draw_end(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_DrawEnd(**raw)
    except Exception as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    db = SessionLocal()
    try:
        element = crud.get_element_by_id(db, msg.element_id, whiteboard_id)
        if not element or element.is_deleted:
            whiteboard_redis.clear_draw_deltas(whiteboard_id, msg.temp_id)
            return
        if element.created_by != user_id:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="FORBIDDEN", message="Cannot finalise another user's stroke.").model_dump(),)
            return
        element = crud.update_element(db, element, updated_by=user_id, data=msg.data, action=ActionType.UPDATE,)
        out = schemas.WS_ElementUpdated(element=schemas.WhiteboardElementOut.model_validate(element),).model_dump()
    except Exception as exc:
        logger.error("draw_end failed board=%s user=%s: %s", whiteboard_id, user_id, exc)
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="UPDATE_FAILED", message="Failed to finalise stroke.").model_dump(),)
        return
    finally:
        db.close()
    whiteboard_redis.clear_draw_deltas(whiteboard_id, msg.temp_id)
    whiteboard_redis.publish_event(whiteboard_id, out)

async def _handle_element_update(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_ElementUpdate(**raw)
    except Exception as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    db = SessionLocal()
    try:
        element = crud.get_element_by_id(db, msg.element_id, whiteboard_id)
        if not element or element.is_deleted:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_NOT_FOUND", message=f"Element {msg.element_id} not found.").model_dump(),)
            return
        if element.is_locked:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_LOCKED", message="Element is locked.").model_dump(),)
            return
        element = crud.update_element(db, element, updated_by=user_id, data=msg.data)
        whiteboard_redis.publish_event(whiteboard_id, schemas.WS_ElementUpdated(
            element=schemas.WhiteboardElementOut.model_validate(element),).model_dump())
    except ValueError as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
    finally:
        db.close()

async def _handle_element_move(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_ElementMove(**raw)
    except Exception as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    db = SessionLocal()
    try:
        element = crud.get_element_by_id(db, msg.element_id, whiteboard_id)
        if not element or element.is_deleted:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_NOT_FOUND", message=f"Element {msg.element_id} not found.").model_dump(),)
            return
        if element.is_locked:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_LOCKED", message="Element is locked.").model_dump(),)
            return
        new_data = dict(element.data)
        if "x" not in new_data or "y" not in new_data:
            await wb_manager.send_to_user(
                whiteboard_id, user_id,
                schemas.WS_Error(code="INVALID_MOVE",message="element_move only supports elements with x/y position.",).model_dump(),)
            return
        new_data["x"] = float(new_data["x"]) + msg.dx
        new_data["y"] = float(new_data["y"]) + msg.dy
        element = crud.update_element(db, element, updated_by=user_id,data=new_data,action=ActionType.MOVE,)
        whiteboard_redis.publish_event(whiteboard_id, schemas.WS_ElementUpdated(
            element=schemas.WhiteboardElementOut.model_validate(element),).model_dump())
    finally:
        db.close()

async def _handle_element_resize(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_ElementResize(**raw)
    except Exception as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    db = SessionLocal()
    try:
        element = crud.get_element_by_id(db, msg.element_id, whiteboard_id)
        if not element or element.is_deleted:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_NOT_FOUND", message=f"Element {msg.element_id} not found.").model_dump(),)
            return
        if element.is_locked:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_LOCKED", message="Element is locked.").model_dump(),)
            return
        element = crud.update_element(db, element, updated_by=user_id,data=msg.data,
                                      action=ActionType.RESIZE,)
        whiteboard_redis.publish_event(whiteboard_id, schemas.WS_ElementUpdated(
            element=schemas.WhiteboardElementOut.model_validate(element),).model_dump())
    finally:
        db.close()

async def _handle_element_delete(raw: dict, whiteboard_id: int, user_id: int) -> None:
    try:
        msg = schemas.WS_ElementDelete(**raw)
    except Exception as exc:
        await wb_manager.send_to_user(whiteboard_id, user_id,
                                      schemas.WS_Error(code="INVALID_PAYLOAD", message=str(exc)).model_dump(),)
        return
    db = SessionLocal()
    try:
        element = crud.get_element_by_id(db, msg.element_id, whiteboard_id)
        if not element or element.is_deleted:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="ELEMENT_NOT_FOUND", message=f"Element {msg.element_id} not found.").model_dump(),)
            return
        if element.is_locked:
            board = crud.get_whiteboard_by_id(db, whiteboard_id)
            from app.project.crud import get_project_role
            role = get_project_role(db, board.project_id, user_id)
            if role not in ("admin", "owner"):
                await wb_manager.send_to_user(
                    whiteboard_id, user_id,
                    schemas.WS_Error(code="ELEMENT_LOCKED",message="Element is locked. Only admins can delete it.",).model_dump(),)
                return
        crud.soft_delete_element(db, element, deleted_by=user_id)
        whiteboard_redis.publish_event(whiteboard_id, schemas.WS_ElementDeleted(element_id=msg.element_id, deleted_by=user_id,).model_dump())
    finally:
        db.close()

async def _handle_undo(whiteboard_id: int, user_id: int) -> None:
    db = SessionLocal()
    try:
        last_action = crud.get_last_user_action(db, whiteboard_id, user_id)
        if not last_action:
            await wb_manager.send_to_user(whiteboard_id, user_id,
                                          schemas.WS_Error(code="NOTHING_TO_UNDO", message="No actions to undo.").model_dump(),)
            return
        element = crud.apply_undo(db, last_action, user_id)
        result = schemas.WS_UndoResult(user_id=user_id, element=schemas.WhiteboardElementOut.model_validate(
            element) if element else None,).model_dump()
        whiteboard_redis.publish_event(whiteboard_id, result)
    finally:
        db.close()

async def _send_init(websocket: WebSocket, whiteboard_id: int, connecting_user_id: int,
                     connecting_user_info: dict,) -> None:
    db = SessionLocal()
    try:
        board = crud.get_whiteboard_by_id(db, whiteboard_id)
        elements = crud.get_live_elements(db, whiteboard_id)
    finally:
        db.close()
    online_users = whiteboard_redis.get_online_users(whiteboard_id)
    cursors = whiteboard_redis.get_all_cursors(whiteboard_id)
    online_ids = {u.get("id") for u in online_users}
    if connecting_user_id not in online_ids:
        online_users = [connecting_user_info] + online_users
    payload = schemas.WS_InitPayload(whiteboard=schemas.WhiteboardOut.model_validate(board),
                                     elements=[schemas.WhiteboardElementOut.model_validate(e) for e in elements],
                                     active_users=[schemas.ActiveUser(user=schemas.UserMini(**u), cursor_x=None, cursor_y=None)
                                                   for u in online_users],cursors=cursors,).model_dump(mode="json")
    await websocket.send_json(payload)

async def _ping_loop(websocket: WebSocket, whiteboard_id: int, user_id: int) -> None:
    try:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            if user_id not in wb_manager.get_local_user_ids(whiteboard_id):
                break
            try:
                await websocket.send_json(schemas.WS_Pong().model_dump())
            except Exception:
                wb_manager.disconnect(whiteboard_id, user_id)
                break
    except asyncio.CancelledError:
        pass

async def _ping_loop(websocket: WebSocket, whiteboard_id: int, user_id: int) -> None:
    try:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            if user_id not in wb_manager.get_local_user_ids(whiteboard_id):
                break
            try:
                await websocket.send_json(schemas.WS_Pong().model_dump())
                whiteboard_redis.refresh_presence_ttl(whiteboard_id)
            except Exception:
                wb_manager.disconnect(whiteboard_id, user_id)
                break
    except asyncio.CancelledError:
        pass

async def _redis_listener(websocket: WebSocket, whiteboard_id: int, user_id: int) -> None:
    loop = asyncio.get_event_loop()
    ps = whiteboard_redis.get_pubsub(whiteboard_id)
    def _poll():
        return ps.get_message(timeout=0.1)
    try:
        while True:
            message = await loop.run_in_executor(None, _poll)
            if message and message.get("type") == "message":
                try:
                    event = json.loads(message["data"])
                    exclude = event.pop("_exclude_user", None)
                    if exclude == user_id:
                        continue
                    await websocket.send_json(event)
                except Exception as exc:
                    logger.warning("Redis relay error board=%s user=%s: %s",whiteboard_id, user_id, exc,)
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass
    finally:
        try:
            ps.unsubscribe()
            ps.close()
        except Exception:
            pass