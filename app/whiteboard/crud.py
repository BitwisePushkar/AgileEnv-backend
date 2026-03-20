import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, joinedload
from app.whiteboard.model import ActionType, Whiteboard, WhiteboardElement, WhiteboardHistory

logger = logging.getLogger(__name__)
HISTORY_RETENTION_DAYS = 30

def get_whiteboard_by_project(db: Session, project_id: int) -> Optional[Whiteboard]:
    return db.query(Whiteboard).filter(Whiteboard.project_id == project_id).first()

def get_whiteboard_by_id(db: Session, whiteboard_id: int) -> Optional[Whiteboard]:
    return db.query(Whiteboard).filter(Whiteboard.id == whiteboard_id).first()

def get_or_create_whiteboard(db: Session, project_id: int) -> Tuple[Whiteboard, bool]:
    board = get_whiteboard_by_project(db, project_id)
    if board:
        return board, False
    board = Whiteboard(project_id=project_id, title="Whiteboard")
    db.add(board)
    try:
        db.commit()
        db.refresh(board)
        logger.info("Created whiteboard project_id=%s id=%s", project_id, board.id)
        return board, True
    except Exception:
        db.rollback()
        board = get_whiteboard_by_project(db, project_id)
        if board:
            return board, False
        raise

def update_whiteboard(db: Session, board: Whiteboard, title: Optional[str] = None, is_locked: Optional[bool] = None,) -> Whiteboard:
    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("Title cannot be blank.")
        if len(title) > 100:
            raise ValueError("Title must be 100 characters or fewer.")
        board.title = title
    if is_locked is not None:
        board.is_locked = is_locked
    db.commit()
    db.refresh(board)
    return board

def get_live_elements(db: Session, whiteboard_id: int) -> List[WhiteboardElement]:
    return (db.query(WhiteboardElement).options(joinedload(WhiteboardElement.creator))
            .filter(WhiteboardElement.whiteboard_id == whiteboard_id,
                    WhiteboardElement.is_deleted == False,)
                    .order_by(WhiteboardElement.z_index, WhiteboardElement.created_at).all())

def get_element_by_id(db: Session, element_id: int, whiteboard_id: Optional[int] = None,) -> Optional[WhiteboardElement]:
    q = db.query(WhiteboardElement).filter(WhiteboardElement.id == element_id)
    if whiteboard_id is not None:
        q = q.filter(WhiteboardElement.whiteboard_id == whiteboard_id)
    return q.first()

def create_element(db: Session, whiteboard_id: int, element_type: str, data: dict, created_by: int,
                   z_index: int = 0,) -> WhiteboardElement:
    if not data:
        raise ValueError("Element data payload cannot be empty.")
    element = WhiteboardElement(whiteboard_id=whiteboard_id, element_type=element_type, data=data,
                                 z_index=z_index, created_by=created_by, updated_by=created_by,)
    db.add(element)
    db.flush()
    db.add(WhiteboardHistory(whiteboard_id=whiteboard_id, element_id=element.id, action_type=ActionType.CREATE,
                             delta={"before": None, "after": data}, performed_by=created_by,))
    db.commit()
    db.refresh(element)
    return element

def update_element(db: Session, element: WhiteboardElement, updated_by: int, data: Optional[dict] = None,
                    z_index: Optional[int] = None, is_locked: Optional[bool] = None, action: ActionType = ActionType.UPDATE,) -> WhiteboardElement:
    before_data = dict(element.data) 
    if data is not None:
        if not data:
            raise ValueError("Element data cannot be empty.")
        element.data = data
    if z_index is not None:
        if z_index < 0:
            raise ValueError("z_index must be >= 0.")
        element.z_index = z_index
    if is_locked is not None:
        element.is_locked = is_locked
    element.updated_by = updated_by
    db.flush()
    db.add(WhiteboardHistory(whiteboard_id=element.whiteboard_id, element_id=element.id, action_type=action,
                              delta={"before": before_data, "after": dict(element.data)}, performed_by=updated_by,))
    db.commit()
    db.refresh(element)
    return element

def soft_delete_element(db: Session, element: WhiteboardElement, deleted_by: int,) -> WhiteboardElement:
    before_data = dict(element.data)
    element.is_deleted = True
    element.updated_by = deleted_by
    db.flush()
    db.add(WhiteboardHistory(whiteboard_id=element.whiteboard_id, element_id=element.id, action_type=ActionType.DELETE,
                             delta={"before": before_data, "after": None},performed_by=deleted_by,))
    db.commit()
    db.refresh(element)
    return element

def clear_all_elements(db: Session, whiteboard_id: int, cleared_by: int) -> int:
    elements = get_live_elements(db, whiteboard_id)
    count = 0
    for el in elements:
        el.is_deleted = True
        el.updated_by = cleared_by
        db.add(WhiteboardHistory(whiteboard_id=whiteboard_id, element_id=el.id, action_type=ActionType.DELETE,
                                 delta={"before": dict(el.data), "after": None}, performed_by=cleared_by,))
        count += 1
    if count:
        db.commit()
    logger.info("Cleared %d elements board=%s by user=%s", count, whiteboard_id, cleared_by)
    return count

def get_last_user_action(db: Session, whiteboard_id: int, user_id: int,) -> Optional[WhiteboardHistory]:
    return (db.query(WhiteboardHistory).filter(WhiteboardHistory.whiteboard_id == whiteboard_id,
                                               WhiteboardHistory.performed_by == user_id, 
                                               WhiteboardHistory.action_type != ActionType.UNDO,)
                                               .order_by(desc(WhiteboardHistory.performed_at)).first())

def apply_undo(db: Session, history_entry: WhiteboardHistory, user_id: int,) -> Optional[WhiteboardElement]:
    element = get_element_by_id(db, history_entry.element_id)
    if element is None:
        logger.warning("Undo skipped — element %s gone (history=%s)",history_entry.element_id, history_entry.id,)
        return None
    action = history_entry.action_type
    before = history_entry.delta.get("before")
    after = history_entry.delta.get("after")
    if action == ActionType.CREATE:
        element.is_deleted = True
        element.updated_by = user_id
    elif action == ActionType.DELETE:
        if before is None:
            logger.warning("Undo DELETE failed — delta.before null history=%s", history_entry.id)
            return None
        element.is_deleted = False
        element.data = before
        element.updated_by = user_id
    elif before is not None:
        element.data = before
        element.updated_by = user_id
    else:
        logger.warning("Undo skipped — delta.before null history=%s", history_entry.id)
        return None
    db.flush()
    db.add(WhiteboardHistory(whiteboard_id=history_entry.whiteboard_id, element_id=history_entry.element_id,
                             action_type=ActionType.UNDO,delta={"before": after,"after": before,"reversed_history_id": history_entry.id,},
                             performed_by=user_id,))
    db.commit()
    db.refresh(element)
    return element

def get_history(db: Session, whiteboard_id: int, user_id: Optional[int] = None, since: Optional[datetime] = None,
                until: Optional[datetime] = None, limit: int = 50, offset: int = 0,) -> Tuple[List[WhiteboardHistory], int]:
    cutoff = since or (datetime.now(timezone.utc) - timedelta(days=HISTORY_RETENTION_DAYS))
    filters = [WhiteboardHistory.whiteboard_id == whiteboard_id, WhiteboardHistory.performed_at >= cutoff,]
    if user_id is not None:
        filters.append(WhiteboardHistory.performed_by == user_id)
    if until is not None:
        filters.append(WhiteboardHistory.performed_at <= until)
    base_q = (db.query(WhiteboardHistory).options(joinedload(WhiteboardHistory.performer))
              .filter(and_(*filters)).order_by(desc(WhiteboardHistory.performed_at)))
    total = base_q.count()
    rows = base_q.offset(offset).limit(min(limit, 200)).all()
    return rows, total

def prune_old_history(db: Session) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_RETENTION_DAYS)
    deleted = (db.query(WhiteboardHistory).filter(WhiteboardHistory.performed_at < cutoff).delete(synchronize_session=False))
    db.commit()
    if deleted:
        logger.info("Pruned %d whiteboard history rows", deleted)
    return deleted