from fastapi import APIRouter,Depends,HTTPException,status,Query,Request
from sqlalchemy.orm import Session
from typing import Optional,List
from app.utils.dbUtil import get_db
from app.auth.models import User
from app.auth.crud import get_user_email,get_user_id
from app.workspace import crud
from app.workspace import schemas
from app.utils import JWTUtil
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.utils.emailUtil import workspace_invitation
from app.workspace.model import Workspace

router=APIRouter()
limiter=Limiter(key_func=get_remote_address)

@router.post("/api/workspace/create/",response_model=schemas.WorkspaceResponse,status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_workspace(request: Request,data:schemas.WorkspaceCreate,db:Session=Depends(get_db),
                     token:str=Depends(JWTUtil.oauth_schema),current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.create_workspace(db,data,current_user.id)
    crud.add_member(db,workspace,current_user,role="admin")
    return workspace

@router.get("/api/workspace/my/",response_model=List[schemas.WorkspaceResponse])
@limiter.limit("50/minute")
def get_my_workspaces(request: Request,db:Session=Depends(get_db),token:str=Depends(JWTUtil.oauth_schema),
                      current_user:User=Depends(JWTUtil.get_user),search:Optional[str]=Query(None,description="Search by workspace name")):
    workspaces=crud.get_user_workspace(db,current_user.id,search)
    for workspace in workspaces:
        workspace.member_count=len(workspace.workspace_member)
    return workspaces

@router.get("/api/workspace/search/", response_model=List[schemas.WorkspaceResponse])
@limiter.limit("100/minute")
def search_workspaces(request: Request,name:str=Query(None, description="workspace name"),db:Session=Depends(get_db),
                      token:str=Depends(JWTUtil.oauth_schema),current_user:User=Depends(JWTUtil.get_user)):
    workspaces=crud.search_workspace(db,current_user.id,name)
    for workspace in workspaces:
        workspace.member_count=len(workspace.workspace_member)
    return workspaces

@router.get("/api/workspace/detail/{name}/", response_model=schemas.WorkspaceWithMembers)
@limiter.limit("100/minute")
def get_workspace(request:Request,name:str,db:Session=Depends(get_db),token:str=Depends(JWTUtil.oauth_schema),
                  current_user:User=Depends(JWTUtil.get_user)):
    workspace = db.query(Workspace).filter(Workspace.name == name).first()
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found")
    if not crud.is_member(db,workspace,current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this workspace")
    return workspace

@router.put("/api/workspace/update/{id}/", response_model=schemas.WorkspaceResponse)
@limiter.limit("10/minute")
def update_workspace(request: Request,id: int,data:schemas.WorkspaceUpdate,db:Session=Depends(get_db),
                     token:str=Depends(JWTUtil.oauth_schema),current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.get_workspace_id(db,id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found")
    if not crud.is_admin(workspace,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only admin can update workspace")
    workspace=crud.update_workspace(db,id,data)
    return workspace

@router.post("/api/workspace/invite/{id}/", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
def invite_users(request: Request,id:int,data:schemas.WorkspaceInvite,db:Session=Depends(get_db),
                 token:str=Depends(JWTUtil.oauth_schema),current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.get_workspace_id(db,id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found")
    if not crud.is_admin(workspace,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only workspace admin can invite users")
    invited = []
    already_members = []
    not_found = []
    for email in data.emails:
        user=get_user_email(db,email)
        if not user:
            not_found.append(email)
            continue
        if crud.is_member(db,workspace,user):
            already_members.append(email)
            continue
        crud.add_member(db,workspace,user)
        workspace_invitation(email=email,name=workspace.name,code=workspace.code,admin=getattr(current_user,"username",current_user.email))
        invited.append(email)
    return {"message": "Invitation process completed","invited": invited,"already_members": already_members,
            "not_found": not_found}

@router.get("/api/workspace/members/{id}",response_model=List[schemas.MemberDetail])
@limiter.limit("10/minute")
def get_workspace_members(request: Request,id:int,db:Session=Depends(get_db),token:str=Depends(JWTUtil.oauth_schema),
                          current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.get_workspace_id(db,id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found")
    if not crud.is_member(db,workspace,current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this workspace")
    members=crud.get_member_details(db,id)
    return members

@router.delete("/api/workspace/{id}/member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
def remove_member(request: Request,id:int,user_id:int,db:Session=Depends(get_db),token:str=Depends(JWTUtil.oauth_schema),
                          current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.get_workspace_id(db,id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found")
    if not crud.is_admin(workspace,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only workspace admin can remove members")
    user=get_user_id(db,user_id)
    if not user or not crud.is_member(db,workspace,user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found in workspace")
    if user.id == workspace.admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot remove workspace admin")
    crud.remove_member(db,workspace,user)
    return None

@router.post("/api/workspace/join/{id}",response_model=schemas.WorkspaceResponse)
@limiter.limit("50/minute")
def join_workspace(request: Request,id:int,code:str,db:Session=Depends(get_db),token:str=Depends(JWTUtil.oauth_schema),
                   current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.get_workspace_id(db,id)
    if not workspace or workspace.code!=code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found or invalid security code")
    if not workspace.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Workspace is not active")
    if crud.is_member(db,workspace,current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are already a member of this workspace")
    crud.add_member(db,workspace,current_user)
    return workspace

@router.delete("/api/workspace/delete/{id}/", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
def delete_workspace(request: Request,id:int,db:Session=Depends(get_db),token:str=Depends(JWTUtil.oauth_schema),
                     current_user:User=Depends(JWTUtil.get_user)):
    workspace=crud.get_workspace_id(db,id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found")
    if not crud.is_admin(workspace,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only admin can delete workspace")
    crud.delete_workspace(db,id)
    return None