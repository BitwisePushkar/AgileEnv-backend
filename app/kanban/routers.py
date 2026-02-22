from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.auth.models import User
from app.project.crud import (get_project_or_404, is_workspace_admin,is_project_member, require_project_role)
from app.kanban import crud, schemas
from app.kanban.models import KanbanCard, KanbanColumn
from slowapi import Limiter
from slowapi.util import get_remote_address

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)

def format_card(card: KanbanCard) -> schemas.CardResponse:
    assignee = None
    if card.assignee:
        assignee = schemas.AssigneeBasic(id=card.assignee.id,username=card.assignee.username,photo=card.assignee.profile.image_url if card.assignee.profile else None,)
    return schemas.CardResponse(id=card.id,project_id=card.project_id,column_id=card.column_id,title=card.title,
                                description=card.description,order=card.order,priority=card.priority.value,assignee=assignee,
                                due_date=card.due_date,is_archived=card.is_archived,created_by=card.created_by,created_at=card.created_at,
                                updated_at=card.updated_at,status=card.status.value,completed_at=card.completed_at,)

def format_column(col: KanbanColumn, include_cards: bool = False) -> schemas.ColumnResponse:
    active_cards = [c for c in col.cards if not c.is_archived]
    base = schemas.ColumnResponse(id=col.id,project_id=col.project_id,name=col.name,order=col.order,color=col.color,
                                  wip_limit=col.wip_limit,is_done_column=col.is_done_column,card_count=len(active_cards),created_at=col.created_at,updated_at=col.updated_at,)
    if include_cards:
        return schemas.ColumnWithCards(**base.model_dump(),cards=[format_card(c) for c in sorted(active_cards, key=lambda c: c.order)],)
    return base

@router.get("/api/projects/{project_id}/kanban/",response_model=schemas.BoardResponse,)
@limiter.limit("60/minute")
def get_board(request: Request,project_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = get_project_or_404(db, project_id)
    crud.assert_kanban_project(project)
    if not is_workspace_admin(db, project.workspace_id, current_user.id):
        if not is_project_member(db, project_id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project")
    columns = crud.get_board(db, project_id)
    col_responses = [format_column(col, include_cards=True) for col in columns]
    total_cards = sum(col.card_count for col in col_responses)
    return schemas.BoardResponse(project_id=project_id,board_type="kanban",columns=col_responses,total_cards=total_cards,)

@router.post("/api/projects/{project_id}/kanban/columns/",response_model=schemas.ColumnResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("30/minute")
def create_column(request: Request,project_id: int,data: schemas.ColumnCreate,db: Session = Depends(get_db),
                  current_user: User = Depends(JWTUtil.get_user),):
    project = get_project_or_404(db, project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    col = crud.create_column(db, project_id,name=data.name,color=data.color,wip_limit=data.wip_limit,)
    return format_column(col)

@router.put("/api/kanban/columns/{column_id}/",response_model=schemas.ColumnResponse,)
@limiter.limit("30/minute")
def update_column(request: Request,column_id: int,data: schemas.ColumnUpdate,db: Session = Depends(get_db),
                  current_user: User = Depends(JWTUtil.get_user),):
    col = crud.get_column_or_404(db, column_id)
    project = get_project_or_404(db, col.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    col = crud.update_column(db, col, data)
    return format_column(col)

@router.delete("/api/kanban/columns/{column_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("10/minute")
def delete_column(request: Request,column_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    col = crud.get_column_or_404(db, column_id)
    project = get_project_or_404(db, col.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="manager")
    crud.delete_column(db, col)
    return {"message": "Column deleted successfully"}

@router.patch("/api/projects/{project_id}/kanban/columns/reorder/",response_model=List[schemas.ColumnResponse],)
@limiter.limit("60/minute")
def reorder_columns(request: Request,project_id: int,data: schemas.ColumnReorder,db: Session = Depends(get_db),
                    current_user: User = Depends(JWTUtil.get_user),):
    project = get_project_or_404(db, project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    columns = crud.reorder_columns(db, project_id, data.column_orders)
    return [format_column(col) for col in columns]

@router.post("/api/kanban/columns/{column_id}/cards/",response_model=schemas.CardResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("60/minute")
def create_card(request: Request,column_id: int,data: schemas.CardCreate,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    col = crud.get_column_or_404(db, column_id)
    project = get_project_or_404(db, col.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    card = crud.create_card(db, column_id, col.project_id, current_user.id, data)
    return format_card(card)

@router.get("/api/kanban/columns/{column_id}/cards/",response_model=List[schemas.CardResponse],)
@limiter.limit("60/minute")
def get_column_cards(request: Request,column_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    col = crud.get_column_or_404(db, column_id)
    project = get_project_or_404(db, col.project_id)
    crud.assert_kanban_project(project)
    if not is_workspace_admin(db, project.workspace_id, current_user.id):
        if not is_project_member(db, col.project_id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project")
    cards = crud.get_column_cards(db, column_id)
    return [format_card(c) for c in cards]

@router.get("/api/kanban/cards/{card_id}/",response_model=schemas.CardResponse,)
@limiter.limit("60/minute")
def get_card(request: Request,card_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    card = crud.get_card_or_404(db, card_id)
    project = get_project_or_404(db, card.project_id)
    crud.assert_kanban_project(project)
    if not is_workspace_admin(db, project.workspace_id, current_user.id):
        if not is_project_member(db, card.project_id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project")
    return format_card(card)

@router.put("/api/kanban/cards/{card_id}/",response_model=schemas.CardResponse,)
@limiter.limit("60/minute")
def update_card(request: Request,card_id: int,data: schemas.CardUpdate,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    card = crud.get_card_or_404(db, card_id)
    project = get_project_or_404(db, card.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    if card.is_archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot edit an archived card. Unarchive it first.",)
    card = crud.update_card(db, card, data)
    return format_card(card)

@router.delete("/api/kanban/cards/{card_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("30/minute")
def delete_card(request: Request,card_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    card = crud.get_card_or_404(db, card_id)
    project = get_project_or_404(db, card.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    crud.delete_card(db, card)
    return {"message": "Card deleted successfully"}

@router.patch("/api/kanban/cards/{card_id}/archive/",response_model=schemas.CardResponse,)
@limiter.limit("30/minute")
def toggle_card_archive(request: Request,card_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    card = crud.get_card_or_404(db, card_id)
    project = get_project_or_404(db, card.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    card = crud.toggle_card_archive(db, card)
    return format_card(card)

@router.patch("/api/kanban/cards/{card_id}/move/",response_model=schemas.CardResponse,)
@limiter.limit("120/minute")
def move_card(request: Request,card_id: int,data: schemas.CardMove,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    card = crud.get_card_or_404(db, card_id)
    project = get_project_or_404(db, card.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    if card.is_archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot move an archived card. Unarchive it first.",)
    dest_col = crud.get_column_or_404(db, data.column_id)
    if dest_col.project_id != card.project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Destination column does not belong to this project",)
    card = crud.move_card(db, card, data.column_id, data.order)
    return format_card(card)

@router.patch("/api/kanban/columns/{column_id}/done/", response_model=schemas.ColumnResponse)
@limiter.limit("10/minute")
def set_done_column(request: Request,column_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    col = crud.get_column_or_404(db, column_id)
    project = get_project_or_404(db, col.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="manager")
    db.query(KanbanColumn).filter(KanbanColumn.project_id == col.project_id,KanbanColumn.is_done_column == True,).update({"is_done_column": False})
    col.is_done_column = True
    db.commit()
    db.refresh(col)
    return format_column(col)

@router.patch("/api/kanban/columns/{column_id}/cards/reorder/",response_model=List[schemas.CardResponse],)
@limiter.limit("120/minute")
def reorder_cards(request: Request,column_id: int,data: schemas.CardReorder,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    col = crud.get_column_or_404(db, column_id)
    project = get_project_or_404(db, col.project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="editor")
    cards = crud.reorder_cards(db, column_id, data.card_orders)
    return [format_card(c) for c in cards]

@router.get("/api/projects/{project_id}/kanban/archived/",response_model=List[schemas.CardResponse],)
@limiter.limit("30/minute")
def get_archived_cards(request: Request,project_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = get_project_or_404(db, project_id)
    crud.assert_kanban_project(project)
    if not is_workspace_admin(db, project.workspace_id, current_user.id):
        if not is_project_member(db, project_id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project")
    cards = crud.get_archived_cards(db, project_id)
    return [format_card(c) for c in cards]

@router.post("/api/projects/{project_id}/kanban/columns/defaults/",response_model=List[schemas.ColumnResponse],status_code=status.HTTP_201_CREATED,)
@limiter.limit("5/minute")
def create_default_columns(request: Request,project_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = get_project_or_404(db, project_id)
    crud.assert_kanban_project(project)
    require_project_role(db, project, current_user.id, minimum_role="manager")
    columns = crud.create_default_columns(db, project_id)
    return [format_column(col) for col in columns]