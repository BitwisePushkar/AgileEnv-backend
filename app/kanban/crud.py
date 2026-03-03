from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime, timezone
from app.kanban.models import KanbanColumn, KanbanCard, CardPriority, CardStatus
from app.kanban import schemas
from app.project.model import Project, ProjectMember
from app.auth.models import User
from app.workspace.model import WorkspaceMember

MIN_ORDER_GAP = 0.001
ORDER_STEP = 1000.0

def assert_kanban_project(project: Project) -> None:
    if project.board_type.value != "kanban":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This project is not a Kanban board",)

def get_next_column_order(db: Session, project_id: int) -> int:
    max_order = (db.query(func.max(KanbanColumn.order)).filter(KanbanColumn.project_id == project_id).scalar())
    return int((max_order or 0) + ORDER_STEP)

def get_next_card_order(db: Session, column_id: int) -> float:
    max_order = (db.query(func.max(KanbanCard.order)).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
                 .scalar())
    return (max_order or 0) + ORDER_STEP

def needs_normalization(db: Session, column_id: int) -> bool:
    orders = [c.order for c in db.query(KanbanCard.order).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
              .order_by(KanbanCard.order).all()]
    if len(orders) < 2:
        return False
    return any((orders[i + 1] - orders[i]) < MIN_ORDER_GAP for i in range(len(orders) - 1))

def normalize_card_order(db: Session, column_id: int) -> None:
    cards = (db.query(KanbanCard).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
             .order_by(KanbanCard.order).all())
    for i, card in enumerate(cards):
        card.order = (i + 1) * ORDER_STEP
    db.commit()

def get_column_or_404(db: Session, column_id: int) -> KanbanColumn:
    col = db.get(KanbanColumn, column_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return col

def get_project_columns(db: Session, project_id: int) -> List[KanbanColumn]:
    return (db.query(KanbanColumn).filter(KanbanColumn.project_id == project_id)
            .order_by(KanbanColumn.order).all())

def get_column_card_count(db: Session, column_id: int) -> int:
    return (db.query(func.count(KanbanCard.id)).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
            .scalar() or 0)

def create_column(db: Session,project_id: int,name: str,color: Optional[str] = None,wip_limit: Optional[int] = None,
                  order: Optional[int] = None,) -> KanbanColumn:
    if order is None:
        order = get_next_column_order(db, project_id)
    col = KanbanColumn(project_id=project_id,
                       name=name,
                       color=color,
                       wip_limit=wip_limit,
                       order=order,)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col

def create_default_columns(db: Session, project_id: int) -> List[KanbanColumn]:
    existing = db.query(KanbanColumn).filter(KanbanColumn.project_id == project_id).count()
    if existing > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Project already has {existing} column(s). Cannot create defaults.",)
    defaults = [
        {"name": "To Do", "color": "#94A3B8", "order": 1000, "is_done_column": False},
        {"name": "In Progress", "color": "#3B82F6", "order": 2000, "is_done_column": False},
        {"name": "Done", "color": "#16A34A", "order": 3000, "is_done_column": True},
        ]
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
    total_count = db.query(KanbanCard).filter(KanbanCard.column_id == col.id).count()
    active_count = (db.query(KanbanCard).filter(KanbanCard.column_id == col.id, KanbanCard.is_archived == False).count())
    if active_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Column has {active_count} active card(s). Move or delete them first.",)
    archived_count = total_count - active_count
    if archived_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=("Delete archieved cards explicitly before deleting the column."),)
    db.delete(col)
    db.commit()

def reorder_columns(db: Session, project_id: int, column_orders: list) -> List[KanbanColumn]:
    project_columns = (db.query(KanbanColumn).filter(KanbanColumn.project_id == project_id).all())
    project_column_ids = {c.id for c in project_columns}
    for item in column_orders:
        if item.column_id not in project_column_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Column {item.column_id} does not belong to this project",)
    TEMP_OFFSET = 1_000_000
    for col in project_columns:
        col.order += TEMP_OFFSET
    db.flush() 
    for item in column_orders:
        col = next(c for c in project_columns if c.id == item.column_id)
        col.order = item.order
    db.commit()
    return get_project_columns(db, project_id)

def get_card_or_404(db: Session, card_id: int) -> KanbanCard:
    card = (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile),joinedload(KanbanCard.creator),)
            .filter(KanbanCard.id == card_id).first())
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card

def get_column_cards(db: Session, column_id: int) -> List[KanbanCard]:
    return (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile))
            .filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False)
            .order_by(KanbanCard.order).all())

def get_board(db: Session, project_id: int) -> List[KanbanColumn]:
    columns = (db.query(KanbanColumn).filter(KanbanColumn.project_id == project_id)
               .order_by(KanbanColumn.order).all())
    for col in columns:
        col._active_cards = (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile))
                             .filter(KanbanCard.column_id == col.id, KanbanCard.is_archived == False)
                             .order_by(KanbanCard.order).all())
    return columns

def count_active_cards(db: Session, column_id: int) -> int:
    return (db.query(KanbanCard).filter(KanbanCard.column_id == column_id, KanbanCard.is_archived == False).count())

def validate_assignee_is_project_member(db: Session, project_id: int, assignee_id: int) -> None:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    is_admin = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == project.workspace_id,WorkspaceMember.user_id == assignee_id,
                                                 WorkspaceMember.role == "admin",).first())
    if is_admin:
        return 
    is_member = (db.query(ProjectMember).filter(ProjectMember.project_id == project_id,
                                                ProjectMember.user_id == assignee_id,).first())
    if not is_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Assignee is not a member of this project",)

def create_card(db: Session,column_id: int,project_id: int,creator_id: int,data,) -> KanbanCard:
    col = get_column_or_404(db, column_id)
    if col.wip_limit is not None:
        current = count_active_cards(db, column_id)
        if current >= col.wip_limit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Column is at WIP limit ({current}/{col.wip_limit}). Move or complete existing cards first.",)
    if data.assignee_id is not None:
        validate_assignee_is_project_member(db, project_id, data.assignee_id)
    order = get_next_card_order(db, column_id)
    card = KanbanCard(project_id = project_id,
                      column_id = column_id,
                      title = data.title,
                      description = data.description,
                      priority = CardPriority(data.priority or "medium"),
                      assignee_id = data.assignee_id,
                      due_date = data.due_date,
                      order = order,
                      created_by = creator_id,)
    db.add(card)
    db.commit()
    return get_card_or_404(db, card.id)

def update_card(db: Session, card: KanbanCard, data, project_id: int) -> KanbanCard:
    updates = data.model_dump(exclude_unset=True)
    if "assignee_id" in updates and updates["assignee_id"] is not None:
        validate_assignee_is_project_member(db, project_id, updates["assignee_id"])
    for field, value in updates.items():
        if field == "priority" and value is not None:
            setattr(card, field, CardPriority(value))
        else:
            setattr(card, field, value)
    db.commit()
    return get_card_or_404(db, card.id)

def move_card(db: Session,card: KanbanCard,dest_column_id: int,new_order: float,) -> KanbanCard:
    dest_col = get_column_or_404(db, dest_column_id)
    if (card.column_id == dest_column_id and abs(card.order - new_order) < MIN_ORDER_GAP):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Card is already at this position",)
    if dest_column_id != card.column_id and dest_col.wip_limit is not None:
        current = count_active_cards(db, dest_column_id)
        if current >= dest_col.wip_limit:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Destination column is at WIP limit ({current}/{dest_col.wip_limit})",)
    src_col_id = card.column_id
    db.query(KanbanCard).filter(KanbanCard.column_id == dest_column_id).with_for_update().all()
    card.order = -1_000_000_000
    db.flush()
    cards_to_shift = (db.query(KanbanCard).filter(KanbanCard.column_id == dest_column_id,KanbanCard.order >= new_order,
                                                  KanbanCard.is_archived == False,).all())
    for c in cards_to_shift:
        c.order += 1_000_000
    db.flush()
    for c in cards_to_shift:
        c.order -= 1_000_000 - ORDER_STEP
    card.column_id = dest_column_id
    card.order = new_order
    if dest_col.is_done_column:
        card.status = CardStatus.COMPLETED
        card.completed_at = datetime.now(timezone.utc)
    elif src_col_id:
        src_col = db.get(KanbanColumn, src_col_id)
        if src_col and src_col.is_done_column and not dest_col.is_done_column:
            card.status = CardStatus.REOPENED
            card.completed_at = None
    db.commit()
    if needs_normalization(db, dest_column_id):
        normalize_card_order(db, dest_column_id)
    if src_col_id and src_col_id != dest_column_id:
        if needs_normalization(db, src_col_id):
            normalize_card_order(db, src_col_id)
    return get_card_or_404(db, card.id)

def reorder_cards(db: Session,column_id: int,card_orders: list) -> List[KanbanCard]:
    submitted_ids = {item.card_id for item in card_orders}
    active_cards = (db.query(KanbanCard).filter(KanbanCard.column_id == column_id,KanbanCard.is_archived == False,)
                    .with_for_update().all())
    active_ids = {c.id for c in active_cards}
    foreign_ids = submitted_ids - active_ids
    if foreign_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Card(s) {sorted(foreign_ids)} do not belong to this column",)
    missing_ids = active_ids - submitted_ids
    if missing_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Reorder list is incomplete. All active cards must be included.",)
    card_map = {c.id: c for c in active_cards}
    TEMP_OFFSET = 1_000_000_000
    for c in active_cards:
        c.order += TEMP_OFFSET
    db.flush()
    for item in card_orders:
        card_map[item.card_id].order = item.order
    db.commit()
    if needs_normalization(db, column_id):
        normalize_card_order(db, column_id)
    return get_column_cards(db, column_id)

def toggle_card_archive(db: Session, card: KanbanCard, restore_column_id: Optional[int] = None) -> KanbanCard:
    if card.is_archived:
        if restore_column_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Provide column_id to specify which column to restore this card into",)
        col = db.get(KanbanColumn, restore_column_id)
        if not col:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restore column not found")
        if col.project_id != card.project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Restore column does not belong to this project",)
        if col.wip_limit is not None:
            current = count_active_cards(db, restore_column_id)
            if current >= col.wip_limit:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Target column is at WIP limit ({current}/{col.wip_limit})",)
        card.column_id = restore_column_id
        card.is_archived = False
        card.order = get_next_card_order(db, restore_column_id)
        card.status = CardStatus.ACTIVE
        card.completed_at = None
    else:
        card.is_archived = True
        card.column_id = None
    db.commit()
    db.refresh(card)
    return card

def delete_card(db: Session, card: KanbanCard) -> None:
    db.delete(card)
    db.commit()

def get_archived_cards(db: Session, project_id: int) -> List[KanbanCard]:
    return (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile))
            .filter(KanbanCard.project_id == project_id, KanbanCard.is_archived == True).order_by(KanbanCard.updated_at.desc()).all())

def search_cards(db: Session, project_id: int, filters: schemas.CardFilterParams) -> List[KanbanCard]:
    query = (db.query(KanbanCard).options(joinedload(KanbanCard.assignee).joinedload(User.profile))
             .filter(KanbanCard.project_id == project_id, KanbanCard.is_archived == False))
    if filters.q:
        query = query.filter(KanbanCard.title.ilike(f"%{filters.q}%"))
    if filters.assignee_id is not None:
        query = query.filter(KanbanCard.assignee_id == filters.assignee_id)
    if filters.priority:
        query = query.filter(KanbanCard.priority == CardPriority(filters.priority))
    if filters.status:
        query = query.filter(KanbanCard.status == CardStatus(filters.status))
    if filters.due_before:
        query = query.filter(KanbanCard.due_date <= filters.due_before)
    if filters.due_after:
        query = query.filter(KanbanCard.due_date >= filters.due_after)
    return query.order_by(KanbanCard.due_date.asc().nulls_last(), KanbanCard.order.asc()).all()

def set_done_column(db: Session, col: KanbanColumn) -> KanbanColumn:
    try:
        db.query(KanbanColumn).filter(KanbanColumn.project_id == col.project_id,KanbanColumn.is_done_column == True,).update({"is_done_column": False})
        col.is_done_column = True
        db.commit()
        db.refresh(col)
        return col
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Failed to update done column",)