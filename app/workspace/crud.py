from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.workspace.model import Workspace, WorkspaceMember, WorkspaceInvite, InviteStatus
from app.auth.models import User, Profile
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import func
from app.workspace import schemas
import logging

logger = logging.getLogger(__name__)

def get_workspace_id(db: Session, id: int) -> Optional[Workspace]:
    return db.query(Workspace).filter(Workspace.id == id).first()

def get_workspace_code(db: Session, code: str) -> Optional[Workspace]:
    return db.query(Workspace).filter(Workspace.code == code).first()

def create_workspace(db: Session, data: schemas.WorkspaceCreate, user_id: int) -> Workspace:
    exist = get_workspace_code(db, data.code)
    if exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Security code is already in use. Please choose a different code.",)
    db_workspace = Workspace(name=data.name,
                             description=data.description,
                             code=data.code,
                             admin_id=user_id,)
    db.add(db_workspace)
    try:
        db.commit()
        db.refresh(db_workspace)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Security code is already in use. Please choose a different code.",)
    return db_workspace

def get_user_workspace(db: Session, user_id: int, search: Optional[str] = None) -> List[Workspace]:
    query = db.query(Workspace).join(WorkspaceMember).filter(WorkspaceMember.user_id == user_id)
    if search:
        search = search.strip()
        try:
            workspace_id = int(search)
            query = query.filter((Workspace.id == workspace_id) | (Workspace.name.ilike(f"%{search}%")))
        except ValueError:
            query = query.filter(Workspace.name.ilike(f"%{search}%"))
    return query.all()

def search_workspace(db: Session, user_id: int, name: Optional[str] = None) -> List[Workspace]:
    query = db.query(Workspace).join(WorkspaceMember).filter(WorkspaceMember.user_id == user_id)
    if name:
        query = query.filter(Workspace.name.ilike(f"%{name.strip()}%"))
    return query.all()

def update_workspace(db: Session, workspace_id: int, data: schemas.WorkspaceUpdate) -> Workspace:
    workspace = get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    update = data.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(workspace, field, value)
    db.commit()
    db.refresh(workspace)
    return workspace

def delete_workspace(db: Session, workspace_id: int) -> bool:
    workspace = get_workspace_id(db, workspace_id)
    if workspace:
        db.delete(workspace)
        db.commit()
        return True
    return False

def is_member(db: Session, workspace: Workspace, user: User) -> bool:
    return (db.query(WorkspaceMember).filter( WorkspaceMember.workspace_id == workspace.id,
                                             WorkspaceMember.user_id == user.id,).first()is not None)

def is_admin(workspace: Workspace, user_id: int) -> bool:
    return workspace.admin_id == user_id

def add_member(db: Session, workspace: Workspace, user: User, role: str = "member") -> WorkspaceMember:
    exist = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                              WorkspaceMember.user_id == user.id,).first())
    if exist:
        return exist
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role)
    db.add(member)
    try:
        db.commit()
        db.refresh(member)
    except IntegrityError:
        db.rollback()
        existing = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                                     WorkspaceMember.user_id == user.id,).first())
        return existing
    return member

def remove_member(db: Session, workspace: Workspace, user: User) -> None:
    member = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                               WorkspaceMember.user_id == user.id,).first())
    if member:
        db.delete(member)
        db.commit()

def get_member(db: Session, workspace: Workspace) -> List[User]:
    members = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).all())
    return [m.user for m in members]

def get_member_details(db: Session, workspace_id: int) -> List[dict]:
    members = (db.query(WorkspaceMember, Profile).outerjoin(Profile, WorkspaceMember.user_id == Profile.user_id)
               .filter(WorkspaceMember.workspace_id == workspace_id).all())
    return [{"id": m.user.id,
             "email": m.user.email,
             "username": getattr(m.user, "username", None),
             "name": profile.name if profile else None,
             "image_url": profile.image_url if profile else None,
             "joined_at": m.joined_at,
             "role": m.role,}for m, profile in members]

def leave_workspace(db: Session, workspace: Workspace, user: User) -> None:
    if workspace.admin_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Admin cannot leave the workspace. Transfer ownership to another member first.",)
    member = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                               WorkspaceMember.user_id == user.id,).first())
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You are not a member of this workspace",)
    db.delete(member)
    db.commit()

def transfer_ownership(db: Session, workspace: Workspace, new_admin: User, current_admin: User) -> Workspace:
    if new_admin.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are already the admin of this workspace",)
    new_admin_member = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                                         WorkspaceMember.user_id == new_admin.id,).first())
    if not new_admin_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Target user is not a member of this workspace",)
    old_admin_member = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                                         WorkspaceMember.user_id == current_admin.id,).first())
    if old_admin_member:
        old_admin_member.role = "member"
    new_admin_member.role = "admin"
    workspace.admin_id = new_admin.id
    db.commit()
    db.refresh(workspace)
    return workspace

def update_member_role(db: Session, workspace: Workspace, target_user: User, new_role: str) -> dict:
    if new_role == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot assign admin role here. Use the transfer ownership endpoint instead.",)
    allowed_roles = {"member"}
    if new_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Invalid role. Allowed roles: {', '.join(allowed_roles)}",)
    member = (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,
                                                WorkspaceMember.user_id == target_user.id,).first())
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User is not a member of this workspace",)
    member.role = new_role
    db.commit()
    db.refresh(member)
    profile = (db.query(Profile).filter(Profile.user_id == target_user.id).first())
    return {"id": member.user.id,
            "email": member.user.email,
            "username": getattr(member.user, "username", None),
            "name": profile.name if profile else None,
            "image_url": profile.image_url if profile else None,
            "joined_at": member.joined_at,
            "role": member.role,}

def count_workspaces(db: Session, user_id: int) -> int:
    return db.query(Workspace).filter(Workspace.admin_id == user_id).count()

def get_all_workspaces(db: Session, skip: int = 0, limit: int = 20, active_only: bool = True) -> List[Workspace]:
    query = db.query(Workspace)
    if active_only:
        query = query.filter(Workspace.is_active == True)
    return query.order_by(Workspace.created_at.desc()).offset(skip).limit(limit).all()

def count_all_workspaces(db: Session, active_only: bool = True) -> int:
    query = db.query(func.count(Workspace.id))
    if active_only:
        query = query.filter(Workspace.is_active == True)
    return query.scalar()

def search_users(db: Session, query: str, limit: int = 20) -> List[dict]:
    search_term = f"%{query.lower()}%"
    results = (db.query(User, Profile).outerjoin(Profile, User.id == Profile.user_id)
               .filter(User.is_active == True,(func.lower(User.username).like(search_term)) | (func.lower(Profile.name).like(search_term)),)
               .limit(limit).all())
    return [{"id": user.id,
             "username": user.username,
             "email": user.email,
             "name": profile.name if profile else None,
             "post": profile.post if profile else None,
             "image_url": profile.image_url if profile else None,}for user, profile in results]

def get_existing_invite(db: Session, workspace_id: int, email: str) -> Optional[WorkspaceInvite]:
    return (db.query(WorkspaceInvite).filter(WorkspaceInvite.workspace_id == workspace_id,WorkspaceInvite.email == email,
                                             WorkspaceInvite.status == InviteStatus.PENDING,).first())

def create_invite(db: Session, workspace_id: int, email: str, invited_by: int) -> WorkspaceInvite:
    existing = get_existing_invite(db, workspace_id, email)
    if existing:
        existing.created_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    invite = WorkspaceInvite(workspace_id=workspace_id,
                             email=email,
                             invited_by=invited_by,
                             status=InviteStatus.PENDING,)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite

def accept_invite(db: Session, workspace_id: int, email: str) -> None:
    invite = get_existing_invite(db, workspace_id, email)
    if invite:
        invite.status = InviteStatus.ACCEPTED
        db.commit()

def get_workspace_or_404(db: Session, workspace_id: int) -> Workspace:
    workspace = get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found",)
    return workspace

def require_workspace_admin(db: Session,workspace: Workspace,user_id: int,) -> None:
    if not is_admin(workspace, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Admin access required",)
    
def is_workspace_member(db: Session,workspace_id: int,user_id: int,) -> bool:
    return (db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id,
                                             WorkspaceMember.user_id == user_id,).first() is not None) 