from sqlalchemy.orm import Session
from app.workspace.model import Workspace,WorkspaceMember
from app.auth.models import User,Profile
from typing import Optional,List
from fastapi import HTTPException,status
from sqlalchemy import func
from app.workspace import schemas

def get_workspace_id(db:Session,id:int):
    return db.query(Workspace).filter(Workspace.id==id).first()

def get_workspace_code(db:Session,code:str):
    return db.query(Workspace).filter(Workspace.code==code).first()

def create_workspace(db:Session,data:schemas.WorkspaceCreate,id:int):
    exist=get_workspace_code(db,data.code)
    if exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Use different code")
    db_workspace=Workspace(name=data.name,description=data.description,code=data.code,admin_id=id)
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

def get_user_workspace(db:Session,id:int,search:Optional[str]=None):
    query=(db.query(Workspace).join(WorkspaceMember).filter(WorkspaceMember.user_id==id))
    if search:
        try:
            workspace_id=int(search)
            query=query.filter((Workspace.id==workspace_id) | (func.lower(Workspace.name) == search.lower()))
        except ValueError:
            query=query.filter(func.lower(Workspace.name) == search.lower())
    return query.all()

def search_workspace(db:Session,id:int,name:Optional[str]=None):
    query=db.query(Workspace)
    if name:
        query=query.filter(func.lower(Workspace.name) == func.lower(name))
    return query.all()

def update_workspace(db:Session,id:int,data:schemas.WorkspaceUpdate):
    workspace=get_workspace_id(db,id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="workspace not found")
    update=data.model_dump(exclude_unset=True)
    for field ,value in update.items():
        setattr(workspace,field,value)
    db.commit()
    db.refresh(workspace)
    return workspace

def add_member(db:Session,workspace:Workspace,user:User,role:str="member"):
    exist=db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id==workspace.id,
                                           WorkspaceMember.user_id==user.id).first()
    if exist:
        return exist
    member=WorkspaceMember(workspace_id=workspace.id,user_id=user.id,role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def remove_member(db:Session,workspace:Workspace,user:User):
    member=db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id==workspace.id,
                                           WorkspaceMember.user_id==user.id).first()
    if member:
        db.delete(member)
        db.commit()

def is_member(db:Session,workspace:Workspace,user:User):
    member=db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id==workspace.id,
                                           WorkspaceMember.user_id==user.id).first()
    return member is not None

def is_admin(workspace:Workspace,id:int)->bool:
    return workspace.admin_id==id

def get_member(db:Session,workspace:Workspace)->List[User]:
    member=db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id).all()
    return [m.user for m in member]

def get_member_details(db:Session,id:int)->List[dict]:
    member=db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id==id).all()
    return [{"id": m.user.id,"email": m.user.email,"username": getattr(m.user, "username", None),
             "joined_at": m.joined_at,"role": m.role,}for m in member]

def delete_workspace(db:Session,id:int):
    workspace=get_workspace_id(db,id)
    if workspace:
        db.delete(workspace)
        db.commit()
        return True
    return False

def count_workspaces(db:Session,id:int)->int:
    count=db.query(Workspace).filter(Workspace.admin_id==id).count()
    return count

def search_users(db:Session,query:str,limit:int=20)->List[dict]:
    search_term = f"%{query.lower()}%"
    results = db.query(User,Profile).outerjoin(Profile,User.id == Profile.user_id).filter(
        (func.lower(User.username).like(search_term)) | (func.lower(Profile.name).like(search_term))).limit(limit).all()
    return [{"id": user.id,"username": user.username,"email": user.email,"name": profile.name if profile else None,"post": profile.post if profile else None,
             "image_url": profile.image_url if profile else None}for user, profile in results]

def get_all_workspaces(db: Session,skip: int = 0,limit: int = 20,active_only: bool = True) -> List[Workspace]:
    query = db.query(Workspace)
    if active_only:
        query = query.filter(Workspace.is_active == True)
    return query.order_by(Workspace.created_at.desc()).offset(skip).limit(limit).all()

def count_all_workspaces(db: Session,active_only: bool = True) -> int:
    query = db.query(func.count(Workspace.id))
    if active_only:
        query = query.filter(Workspace.is_active == True)
    return query.scalar()

def leave_workspace(db: Session,workspace: Workspace,user: User):
    if workspace.admin_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Admin cannot leave the workspace. Transfer ownership to another member first.")

    member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,WorkspaceMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="You are not a member of this workspace")

    db.delete(member)
    db.commit()

def transfer_ownership(db: Session,workspace: Workspace,new_admin: User,current_admin: User):
    new_admin_member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,WorkspaceMember.user_id == new_admin.id).first()

    if not new_admin_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Target user is not a member of this workspace")

    if new_admin.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are already the admin of this workspace")

    workspace.admin_id = new_admin.id

    old_admin_member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,WorkspaceMember.user_id == current_admin.id).first()
    if old_admin_member:
        old_admin_member.role = "member"
    new_admin_member.role = "admin"
    db.commit()
    db.refresh(workspace)
    return workspace

def update_member_role(db: Session, workspace: Workspace, target_user: User, new_role: str) -> dict:
    allowed_roles = {"member", "admin"}
    if new_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Invalid role. Allowed roles: {', '.join(allowed_roles)}")

    member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,WorkspaceMember.user_id == target_user.id).first()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User is not a member of this workspace")

    if new_role == "admin":
        workspace.admin_id = target_user.id
        current_admin_member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace.id,WorkspaceMember.user_id == workspace.admin_id).first()
        if current_admin_member:
            current_admin_member.role = "member"
    member.role = new_role
    db.commit()
    db.refresh(member)
    return {"id": member.user.id,"email": member.user.email,"username": getattr(member.user, "username", None),
            "joined_at": member.joined_at,"role": member.role,}