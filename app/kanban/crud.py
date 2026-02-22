from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime, timezone
from app.kanban.models import KanbanColumn, KanbanCard, CardPriority, CardStatus
from app.project.model import Project
from app.auth.models import User

MIN_ORDER_GAP = 0.001
ORDER_STEP = 1000.0 

def assert_kanban_project(project: Project) -> None:
    if project.board_type.value != "kanban":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"This project is not Kanban",)

def normalize_card_order(db: Session, column_id: int) -> None:
    cards = (db.query(KanbanCard).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
             .order_by(KanbanCard.order).all())
    for i, card in enumerate(cards):
        card.order = (i + 1) * ORDER_STEP
    db.commit()

def needs_normalization(db: Session, column_id: int) -> bool:
    cards = (db.query(KanbanCard.order).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
             .order_by(KanbanCard.order).all())
    orders = [c.order for c in cards]
    if len(orders) < 2:
        return False
    return any((orders[i+1] - orders[i]) < MIN_ORDER_GAP for i in range(len(orders)-1))

def get_next_column_order(db: Session, project_id: int) -> int:
    max_order = db.query(func.max(KanbanColumn.order)).filter(KanbanColumn.project_id == project_id).scalar()
    return int((max_order or 0) + ORDER_STEP)

def get_next_card_order(db: Session, column_id: int) -> float:
    max_order = db.query(func.max(KanbanCard.order)).filter(KanbanCard.column_id == column_id,KanbanCard.is_archived == False,).scalar()
    return (max_order or 0) + ORDER_STEP

def get_column_or_404(db: Session, column_id: int) -> KanbanColumn:
    col = db.get(KanbanColumn, column_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return col

def get_project_columns(db: Session, project_id: int) -> List[KanbanColumn]:
    return (db.query(KanbanColumn).filter(KanbanColumn.project_id == project_id)
            .order_by(KanbanColumn.order).all())

def create_column(db: Session,project_id: int,name: str,color: Optional[str] = None,wip_limit: Optional[int] = None,
                  order: Optional[int] = None,) -> KanbanColumn:
    if order is None:
        order = get_next_column_order(db, project_id)
    col = KanbanColumn(project_id=project_id,name=name,color=color,wip_limit=wip_limit,order=order,)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col

def create_default_columns(db: Session, project_id: int) -> List[KanbanColumn]:
    defaults = [
        {"name": "To Do", "color": "#94A3B8", "order": 1000, "is_done_column": False},
        {"name": "In Progress", "color": "#3B82F6", "order": 2000, "is_done_column": False},
        {"name": "Done", "color": "#16A34A", "order": 3000, "is_done_column": True},
        ]
    existing = db.query(KanbanColumn).filter(KanbanColumn.project_id == project_id).count()
    if existing > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Project already has {existing} column(s).",)
    columns = []
    for d in defaults:
        col = KanbanColumn(project_id=project_id, **d)
        db.add(col)
        columns.append(col)
    db.commit()
    for col in columns:
        db.refresh(col)
    return columns

def update_column(db: Session, col: KanbanColumn, data) -> KanbanColumn:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(col, field, value)
    db.commit()
    db.refresh(col)
    return col

def delete_column(db: Session, col: KanbanColumn) -> None:
    active_count = db.query(KanbanCard).filter(KanbanCard.column_id == col.id,KanbanCard.is_archived == False,).count()
    if active_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Column has {active_count} active card(s).",)
    db.delete(col)
    db.commit()

def reorder_columns(db: Session, project_id: int, column_orders: List[dict]) -> List[KanbanColumn]:
    project_column_ids = {c.id for c in db.query(KanbanColumn.id).filter(KanbanColumn.project_id == project_id).all()}
    for item in column_orders:
        if item["column_id"] not in project_column_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Column {item['column_id']} does not belong to this project",)
    for item in column_orders:
        col = db.get(KanbanColumn, item["column_id"])
        col.order = item["order"]
    db.commit()
    return get_project_columns(db, project_id)

def count_active_cards(db: Session, column_id: int) -> int:
    return db.query(KanbanCard).filter(KanbanCard.column_id == column_id,KanbanCard.is_archived == False, ).count()

def get_card_or_404(db: Session, card_id: int) -> KanbanCard:
    card = (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile),joinedload(KanbanCard.creator),)
            .filter(KanbanCard.id == card_id).first())
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card

def get_column_cards(db: Session, column_id: int) -> List[KanbanCard]:
    return (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile))
            .filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False).order_by(KanbanCard.order)
            .all())

def get_board(db: Session, project_id: int) -> List[KanbanColumn]:
    return (db.query(KanbanColumn).options(joinedload(KanbanColumn.cards).joinedload(KanbanCard.assignee).joinedload(User.profile))
            .filter(KanbanColumn.project_id == project_id).order_by(KanbanColumn.order).all())

def create_card(db: Session,column_id: int,project_id: int,creator_id: int,data,) -> KanbanCard:
    col = get_column_or_404(db, column_id)
    if col.wip_limit is not None:
        current = count_active_cards(db, column_id)
        if current >= col.wip_limit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"This column is at WIP limit ({current}/{col.wip_limit}). ")
    order = get_next_card_order(db, column_id)
    card = KanbanCard(project_id=project_id,column_id=column_id,title=data.title,description=data.description,
                      priority=CardPriority(data.priority or "medium"),assignee_id=data.assignee_id,due_date=data.due_date,
                      order=order,created_by=creator_id,)
    db.add(card)
    db.commit()
    return get_card_or_404(db, card.id)

def update_card(db: Session, card: KanbanCard, data) -> KanbanCard:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field == "priority" and value is not None:
            setattr(card, field, CardPriority(value))
        else:
            setattr(card, field, value)
    db.commit()
    return get_card_or_404(db, card.id)

def move_card(db: Session,card: KanbanCard,dest_column_id: int,new_order: float,) -> KanbanCard:
    dest_col = get_column_or_404(db, dest_column_id)
    if card.column_id == dest_column_id and abs(card.order - new_order) < MIN_ORDER_GAP:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Card is already in this position",)
    if dest_column_id != card.column_id and dest_col.wip_limit is not None:
        current = count_active_cards(db, dest_column_id)
        if current >= dest_col.wip_limit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Column is at WIP limit ")
    src_col = db.get(KanbanColumn, card.column_id) if card.column_id else None
    card.column_id = dest_column_id
    card.order = new_order
    if dest_col.is_done_column:
        card.status = CardStatus.COMPLETED
        card.completed_at = datetime.now(timezone.utc)
    elif src_col and src_col.is_done_column and not dest_col.is_done_column:
        card.status = CardStatus.REOPENED
        card.completed_at = None 
    db.commit()
    if needs_normalization(db, dest_column_id):
        normalize_card_order(db, dest_column_id)
        db.refresh(card)
    if src_col and src_col.id != dest_column_id:
        if needs_normalization(db, src_col.id):
            normalize_card_order(db, src_col.id)
    return get_card_or_404(db, card.id)

def reorder_cards(db: Session,column_id: int,card_orders: List[dict],) -> List[KanbanCard]:
    column_card_ids = {c.id for c in db.query(KanbanCard.id).filter(KanbanCard.column_id == column_id).all()}
    for item in card_orders:
        if item["card_id"] not in column_card_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Card {item['card_id']} does not belong to this column",)
    for item in card_orders:
        card = db.get(KanbanCard, item["card_id"])
        card.order = item["order"]
    db.commit()
    if needs_normalization(db, column_id):
        normalize_card_order(db, column_id)
    return get_column_cards(db, column_id)

def toggle_card_archive(db: Session, card: KanbanCard) -> KanbanCard:
    card.is_archived = not card.is_archived
    if card.is_archived:
        card.column_id = None
    db.commit()
    db.refresh(card)
    return card

def delete_card(db: Session, card: KanbanCard) -> None:
    db.delete(card)
    db.commit()

def get_archived_cards(db: Session, project_id: int) -> List[KanbanCard]:
    return (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile))
            .filter(KanbanCard.project_id == project_id, KanbanCard.is_archived == True) .order_by(KanbanCard.updated_at.desc()).all())