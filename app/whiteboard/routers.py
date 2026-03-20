import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from sqlalchemy.orm import Session
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.auth.models import User
from app.project.crud import get_project_or_404, get_project_role, is_project_member
from app.whiteboard import crud
from app.utils.redis.whiteboard_redis import get_online_users,publish_event, get_all_cursors
from app.utils.websocket.whiteboard import whiteboard_ws_endpoint
from app.whiteboard import schemas

logger = logging.getLogger(__name__)
router = APIRouter()

def _require_project_member(db: Session, project_id: int, user_id: int) -> None:
    if not is_project_member(db, project_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project.",)

def _require_project_admin(db: Session, project_id: int, user_id: int) -> None:
    role = get_project_role(db, project_id, user_id)
    if role not in ("admin", "owner", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only project admins can perform this action.",)

def _require_board_unlocked(board, project_id: int, db: Session, user_id: int) -> None:
    if board.is_locked:
        role = get_project_role(db, project_id, user_id)
        if role not in ("admin", "owner", "manager"):
            raise HTTPException(status_code=status.HTTP_423_LOCKED,detail="This whiteboard is locked. Only admins can make changes.",)

def _get_board_or_404(db: Session, whiteboard_id: int):
    board = crud.get_whiteboard_by_id(db, whiteboard_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Whiteboard {whiteboard_id} not found.",)
    return board

@router.get("/api/projects/{project_id}/whiteboard/",response_model=schemas.WhiteboardOut,)
def get_or_create_whiteboard(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(JWTUtil.get_user),):
    project = get_project_or_404(db, project_id)
    _require_project_member(db, project_id, current_user.id)
    if project.is_archived:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Cannot open whiteboard of an archived project.",)
    board, _ = crud.get_or_create_whiteboard(db, project_id)
    return schemas.WhiteboardOut.model_validate(board)

@router.patch("/api/whiteboards/{whiteboard_id}/",response_model=schemas.WhiteboardOut,)
def update_whiteboard(whiteboard_id: int, body: schemas.WhiteboardUpdate, db: Session = Depends(get_db),
                       current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    if body.is_locked is not None:
        _require_project_admin(db, board.project_id, current_user.id)
    try:
        board = crud.update_whiteboard(db, board, title=body.title, is_locked=body.is_locked)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if body.is_locked is not None:
        publish_event(whiteboard_id, schemas.WS_BoardLocked(is_locked=body.is_locked,
                                                            by_user=current_user.id,).model_dump())
    return schemas.WhiteboardOut.model_validate(board)

@router.delete("/api/whiteboards/{whiteboard_id}/clear/",)
def clear_whiteboard(whiteboard_id: int, db: Session = Depends(get_db), current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_admin(db, board.project_id, current_user.id)
    count = crud.clear_all_elements(db, whiteboard_id, cleared_by=current_user.id)
    publish_event(whiteboard_id, {"type": "board_cleared", "cleared_by": current_user.id, "count": count})
    return {"message": f"Cleared {count} elements.", "count": count}

@router.get("/api/whiteboards/{whiteboard_id}/elements/",response_model=schemas.ElementsBulkOut,)
def list_elements(whiteboard_id: int, db: Session = Depends(get_db), current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    elements = crud.get_live_elements(db, whiteboard_id)
    return schemas.ElementsBulkOut(whiteboard_id=whiteboard_id,elements=[schemas.WhiteboardElementOut.model_validate(e) for e in elements],
                                   total=len(elements),)

@router.post("/api/whiteboards/{whiteboard_id}/elements/",response_model=schemas.WhiteboardElementOut,
             status_code=status.HTTP_201_CREATED,)
def create_element(whiteboard_id: int, body: schemas.WhiteboardElementCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    _require_board_unlocked(board, board.project_id, db, current_user.id)
    try:
        element = crud.create_element(db, whiteboard_id=whiteboard_id, element_type=body.element_type.value,
                                      data=body.data, created_by=current_user.id, z_index=body.z_index,)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    out = schemas.WhiteboardElementOut.model_validate(element)
    publish_event(whiteboard_id, schemas.WS_ElementCreated(element=out).model_dump())
    return out

@router.get("/api/whiteboards/{whiteboard_id}/elements/{element_id}/",response_model=schemas.WhiteboardElementOut,)
def get_element(whiteboard_id: int, element_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    element = crud.get_element_by_id(db, element_id, whiteboard_id)
    if not element or element.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Element {element_id} not found.",)
    return schemas.WhiteboardElementOut.model_validate(element)

@router.patch("/api/whiteboards/{whiteboard_id}/elements/{element_id}/",response_model=schemas.WhiteboardElementOut,)
def update_element(whiteboard_id: int, element_id: int, body: schemas.WhiteboardElementUpdate,
                   db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    _require_board_unlocked(board, board.project_id, db, current_user.id)
    element = crud.get_element_by_id(db, element_id, whiteboard_id)
    if not element or element.is_deleted:
        raise HTTPException(status_code=404, detail=f"Element {element_id} not found.")
    if element.is_locked and body.is_locked is None:
        _require_project_admin(db, board.project_id, current_user.id)
    if body.is_locked is not None:
        _require_project_admin(db, board.project_id, current_user.id)
    try:
        element = crud.update_element(db, element, updated_by=current_user.id, data=body.data, z_index=body.z_index,
                                      is_locked=body.is_locked,)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    out = schemas.WhiteboardElementOut.model_validate(element)
    publish_event(whiteboard_id, schemas.WS_ElementUpdated(element=out).model_dump())
    return out

@router.delete("/api/whiteboards/{whiteboard_id}/elements/{element_id}/", status_code=status.HTTP_204_NO_CONTENT,)
def delete_element(whiteboard_id: int, element_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    _require_board_unlocked(board, board.project_id, db, current_user.id)
    element = crud.get_element_by_id(db, element_id, whiteboard_id)
    if not element or element.is_deleted:
        raise HTTPException(status_code=404, detail=f"Element {element_id} not found.")
    if element.is_locked:
        _require_project_admin(db, board.project_id, current_user.id)
    crud.soft_delete_element(db, element, deleted_by=current_user.id)
    publish_event(whiteboard_id, schemas.WS_ElementDeleted(element_id=element_id, 
                                                           deleted_by=current_user.id,).model_dump())

@router.get("/api/whiteboards/{whiteboard_id}/history/", response_model=schemas.WhiteboardHistoryListOut,)
def get_history(whiteboard_id: int, user_id: Optional[int] = Query(None, description="Filter by user"),
                since: Optional[datetime] = Query(None, description="ISO-8601 lower bound"),
                until: Optional[datetime] = Query(None, description="ISO-8601 upper bound"),
                limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db),
                current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    rows, total = crud.get_history(db, whiteboard_id=whiteboard_id, user_id=user_id, since=since, until=until,
                                    limit=limit, offset=offset,)
    return schemas.WhiteboardHistoryListOut(whiteboard_id=whiteboard_id, entries=[schemas.WhiteboardHistoryOut.model_validate(r) for r in rows],
                                            total=total,)

@router.get("/api/whiteboards/{whiteboard_id}/presence/", response_model=schemas.ActiveUsersOut,)
def get_presence(whiteboard_id: int, db: Session = Depends(get_db), current_user: User = Depends(JWTUtil.get_user),):
    board = _get_board_or_404(db, whiteboard_id)
    _require_project_member(db, board.project_id, current_user.id)
    online = get_online_users(whiteboard_id)
    cursors = {str(c["user_id"]): c for c in get_all_cursors(whiteboard_id)}
    active = []
    for u in online:
        cursor = cursors.get(str(u.get("id", "")), {})
        active.append(schemas.ActiveUser(user=schemas.UserMini(id=u["id"], username=u["username"]),cursor_x=cursor.get("x"),
                                         cursor_y=cursor.get("y"),))
    return schemas.ActiveUsersOut(whiteboard_id=whiteboard_id, active_users=active, count=len(active),)

@router.websocket("/ws/whiteboard/{whiteboard_id}")
async def wb_ws(websocket: WebSocket, whiteboard_id: int, token: str = Query(..., description="JWT access token"),):
    await whiteboard_ws_endpoint(websocket, whiteboard_id, token)