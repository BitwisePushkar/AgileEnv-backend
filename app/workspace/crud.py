from sqlalchemy.orm import Session
from app.workspace.model import Workspace,WorkspaceMember
from app.auth.models import User
from typing import Optional,List
from fastapi import HTTPException,status
from sqlalchemy import func
from app.workspace import schemas

def get_workspace_id(db:Session,id:str):
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
    query=db.query(Workspace).join(WorkspaceMember).filter(WorkspaceMember.user_id==id)
    if name:
        query=query.filter(func.lower(Workspace.name) == func.lower(name))
    return query.all()

def update_workspace(db:Session,id:int,data:schemas.WorkspaceUpdate):
    workspace=get_workspace_id(db,id)
    if not workspace:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="workspace not found")
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