from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.dbUtil import get_db
from app.auth.models import User
from app.auth.crud import get_user_email, get_user_id, get_profile_id
from app.workspace import crud, schemas
from app.utils import JWTUtil
from app.utils.email import workspace_invitation, workspace_welcome, workspace_invitation_new_user
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

FREE_TIER_WORKSPACE_LIMIT = 2
MAX_INVITE_BATCH = 20

@router.post("/api/workspace/create/",response_model=schemas.WorkspaceResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("20/minute")
def create_workspace(request: Request,data: schemas.WorkspaceCreate,db: Session = Depends(get_db),
                     current_user: User = Depends(JWTUtil.get_user),):
    count = crud.count_workspaces(db, current_user.id)
    if count >= FREE_TIER_WORKSPACE_LIMIT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Free plan allows up to {FREE_TIER_WORKSPACE_LIMIT} workspaces. Please upgrade to create more.",)
    workspace = crud.create_workspace(db, data, current_user.id)
    crud.add_member(db, workspace, current_user, role="admin")
    logger.info(f"Workspace created: id={workspace.id} by user_id={current_user.id}")
    return workspace

@router.get("/api/workspace/search/",response_model=List[schemas.WorkspaceResponse],)
@limiter.limit("100/minute")
def search_workspaces(request: Request,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),
                      search: Optional[str] = Query(None, description="Partial workspace name search"),
                      all: bool = Query(False,description="If true, searches all user's workspaces by name. If false, returns user's workspaces.",),):
    if all:
        return crud.search_workspace(db, current_user.id, search)
    return crud.get_user_workspace(db, current_user.id, search)

@router.get("/api/workspace/detail/{workspace_id}/",response_model=schemas.WorkspaceWithMembers,)
@limiter.limit("100/minute")
def get_workspace(request: Request,workspace_id: int,db: Session = Depends(get_db),
                  current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_member(db, workspace, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this workspace",)
    return workspace

@router.put("/api/workspace/update/{workspace_id}/",response_model=schemas.WorkspaceResponse,)
@limiter.limit("10/minute")
def update_workspace(request: Request,workspace_id: int,data: schemas.WorkspaceUpdate,db: Session = Depends(get_db),
                     current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_admin(workspace, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the workspace admin can update workspace details",)
    updated = crud.update_workspace(db, workspace_id, data)
    logger.info(f"Workspace updated: id={workspace_id} by user_id={current_user.id}")
    return updated

@router.delete("/api/workspace/delete/{workspace_id}/",status_code=status.HTTP_204_NO_CONTENT,)
@limiter.limit("10/minute")
def delete_workspace(request: Request,workspace_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_admin(workspace, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the workspace admin can delete this workspace",)
    crud.delete_workspace(db, workspace_id)
    logger.info(f"Workspace deleted: id={workspace_id} by user_id={current_user.id}")
    return {"message": "Successfully deleted the workspace",}

@router.get("/api/workspace/members/{workspace_id}/",response_model=List[schemas.MemberDetail],)
@limiter.limit("30/minute")
def get_workspace_members(request: Request,workspace_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_member(db, workspace, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this workspace",)
    return crud.get_member_details(db, workspace_id)

@router.post("/api/workspace/invite/{id}/")
def invite_users(request: Request,id: int,data: schemas.InviteRequest,background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_or_404(db, id)
    crud.require_workspace_admin(db, workspace, current_user.id)
    unique_emails = list(set(e.lower().strip() for e in data.emails))
    if len(unique_emails) > MAX_INVITE_BATCH:
        raise HTTPException(400, f"Maximum {MAX_INVITE_BATCH} emails per invite batch")
    invited_existing = []
    invited_new = []
    already_members = []
    unique_emails = [e for e in unique_emails if e != current_user.email.lower()]
    if current_user.email.lower() not in [e.lower() for e in unique_emails]:
        already_members.append(current_user.email)
    admin_username = current_user.username or current_user.email
    lang = "en"
    for email in unique_emails:
        user = get_user_email(db, email)
        if user and crud.is_workspace_member(db, id, user.id):
            already_members.append(email)
            continue
        crud.create_invite(db, id, email, current_user.id)
        if user:
            invited_existing.append(email)
            background_tasks.add_task(workspace_invitation,
                                      email=email,
                                      name=workspace.name,
                                      code=workspace.code,
                                      admin=admin_username,
                                      language=lang,)
        else:
            invited_new.append(email)
            background_tasks.add_task(workspace_invitation_new_user, 
                                      email=email,
                                      name=workspace.name,
                                      code=workspace.code,
                                      admin=admin_username,)
    return schemas.InviteResponse(message="Invitations sent",
                                  invited_existing=invited_existing,
                                  invited_new=invited_new,
                                  already_members=already_members,)

@router.post("/api/workspace/join/{workspace_id}/",response_model=schemas.WorkspaceResponse,)
@limiter.limit("20/minute")
def join_workspace(request: Request,workspace_id: int,data: schemas.JoinWorkspace,background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace or workspace.code != data.code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Workspace not found or invalid security code",)
    if not workspace.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="This workspace is currently inactive",)
    if crud.is_member(db, workspace, current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are already a member of this workspace",)
    crud.add_member(db, workspace, current_user)
    crud.accept_invite(db, workspace_id, current_user.email)
    logger.info(f"User {current_user.id} joined workspace {workspace_id}")
    user_profile = get_profile_id(db, current_user.id)
    user_lang = user_profile.language if user_profile and user_profile.language else "en"
    admin_user = get_user_id(db, workspace.admin_id)
    admin_username = (getattr(admin_user, "username", None) or admin_user.email
                      if admin_user else "Workspace Admin")
    background_tasks.add_task(
        workspace_welcome,
        email=current_user.email,
        username=getattr(current_user, "username", None) or current_user.email,
        workspace_name=workspace.name,
        workspace_description=workspace.description or "",
        admin_username=admin_username,
        member_count=workspace.member_count,
        joined_at=datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC"),
        language=user_lang,
    )
    return workspace

@router.delete("/api/workspace/{workspace_id}/member/{user_id}/",status_code=status.HTTP_204_NO_CONTENT,)
@limiter.limit("30/minute")
def remove_member(request: Request,workspace_id: int,user_id: int,db: Session = Depends(get_db),
                  current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_admin(workspace, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the workspace admin can remove members",)
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You cannot remove yourself. Use the leave endpoint or transfer ownership first.",)
    user = get_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not crud.is_member(db, workspace, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User is not a member of this workspace",)
    if user.id == workspace.admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot remove the workspace admin. Transfer ownership first.",)
    crud.remove_member(db, workspace, user)
    logger.info(f"User {user_id} removed from workspace {workspace_id} by admin {current_user.id}")
    return {"message": "Successfully removed from workspace"}

@router.delete("/api/workspace/{workspace_id}/leave/",status_code=status.HTTP_200_OK,)
@limiter.limit("20/minute")
def leave_workspace(request: Request,workspace_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    crud.leave_workspace(db, workspace, current_user)
    logger.info(f"User {current_user.id} left workspace {workspace_id}")
    return {"message": "You have successfully left the workspace"}

@router.put("/api/workspace/{workspace_id}/transfer/",response_model=schemas.WorkspaceResponse,)
@limiter.limit("10/minute")
def transfer_ownership(request: Request,workspace_id: int,data: schemas.TransferOwnership,db: Session = Depends(get_db),
                       current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_admin(workspace, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the current admin can transfer ownership",)
    if data.new_admin_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are already the admin of this workspace",)
    new_admin = get_user_id(db, data.new_admin_id)
    if not new_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
    if not new_admin.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot transfer ownership to an inactive user",)
    if not crud.is_member(db, workspace, new_admin):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Target user is not a member of this workspace",)
    workspace = crud.transfer_ownership(db, workspace, new_admin, current_user)
    logger.info(f"Ownership of workspace {workspace_id} transferred from {current_user.id} to {new_admin.id}")
    return workspace

@router.patch("/api/workspace/{workspace_id}/member/{user_id}/role/",response_model=schemas.MemberDetail,)
@limiter.limit("20/minute")
def update_member_role(request: Request,workspace_id: int,user_id: int,data: schemas.UpdateMemberRole,
                       db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    workspace = crud.get_workspace_id(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if not crud.is_admin(workspace, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the workspace admin can update member roles",)
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You cannot change your own role. Use the transfer ownership endpoint instead.",)
    target_user = get_user_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.update_member_role(db, workspace, target_user, data.role)

@router.get("/api/users/search/",response_model=List[schemas.UserSearchResponse],)
@limiter.limit("100/minute")
def search_users(request: Request,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),
                 query: Optional[str] = Query(None, description="Search by username or display name"),
                 limit: int = Query(20, ge=1, le=100, description="Max results to return"),):
    if not query or not query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Search query is required",)
    return crud.search_users(db, query.strip(), limit)

@router.get("/api/workspace/list/",response_model=schemas.PaginatedWorkspaceResponse,)
@limiter.limit("60/minute")
def list_workspaces(request: Request,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),
                    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
                    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
                    active_only: bool = Query(True, description="Only return active workspaces"),):
    skip = (page - 1) * page_size
    workspaces = crud.get_user_workspace(db, current_user.id)
    total = len(workspaces)
    paginated = workspaces[skip: skip + page_size]
    return {"total": total,
            "page": page,
            "page_size": page_size,
            "results": paginated,}