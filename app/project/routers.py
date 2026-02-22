from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.auth.models import User
from app.auth.crud import get_user_id
from app.project import crud, schemas
from app.project.model import Project
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.kanban.crud import create_default_columns as create_kanban_defaults

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)

def format_project(project: Project) -> schemas.ProjectResponse:
    return schemas.ProjectResponse(id=project.id,workspace_id=project.workspace_id,name=project.name,description=project.description,
                                   icon=project.icon,color=project.color,board_type=project.board_type.value,
                                   is_archived=project.is_archived,created_by=project.created_by,created_at=project.created_at,
                                   updated_at=project.updated_at,member_count=len(project.members),)

def format_project_detail(project: Project) -> schemas.ProjectDetailResponse:
    members = [schemas.ProjectMemberBasic(id=m.user.id,username=m.user.username,photo=m.user.profile.image_url if m.user.profile else None,
                                          role=m.role,)for m in project.members]
    return schemas.ProjectDetailResponse(id=project.id,workspace_id=project.workspace_id,name=project.name,description=project.description,
                                         icon=project.icon,color=project.color,board_type=project.board_type.value,is_archived=project.is_archived,created_by=project.created_by,
                                         created_at=project.created_at,updated_at=project.updated_at,member_count=len(project.members),members=members,)

@router.post("/api/workspace/{workspace_id}/projects/",response_model=schemas.ProjectDetailResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("20/minute")
def create_project(request: Request,workspace_id: int,data: schemas.ProjectCreate,db: Session = Depends(get_db),
                   current_user: User = Depends(JWTUtil.get_user),):
    if not crud.is_workspace_member(db, workspace_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You must be a workspace member to create a project",)
    project = crud.create_project(db, workspace_id, data, current_user.id)
    if data.board_type == "kanban":
        create_kanban_defaults(db, project.id)
    return format_project_detail(project)

@router.get("/api/workspace/{workspace_id}/projects/",response_model=List[schemas.ProjectResponse],)
@limiter.limit("60/minute")
def list_projects(request: Request,workspace_id: int,include_archived: bool = Query(False, description="Include archived projects"),
                  db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    if not crud.is_workspace_member(db, workspace_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You must be a workspace member to view projects",)
    projects = crud.list_projects(db, workspace_id, current_user.id, include_archived)
    return [format_project(p) for p in projects]

@router.get("/api/projects/{id}/",response_model=schemas.ProjectDetailResponse,)
@limiter.limit("60/minute")
def get_project(request: Request,id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    if not crud.is_workspace_admin(db, project.workspace_id, current_user.id):
        if not crud.is_project_member(db, id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project",)
    return format_project_detail(project)

@router.put("/api/projects/{id}/",response_model=schemas.ProjectDetailResponse,)
@limiter.limit("20/minute")
def update_project(request: Request,id: int,data: schemas.ProjectUpdate,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    project = crud.update_project(db, project, data)
    return format_project_detail(project)

@router.delete("/api/projects/{id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("10/minute")
def delete_project(request: Request,id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    is_admin = crud.is_workspace_admin(db, project.workspace_id, current_user.id)
    is_creator = project.created_by == current_user.id
    if not is_admin and not is_creator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the project creator or workspace admin can delete this project",)
    crud.delete_project(db, project)
    return {"message": "Project deleted successfully"}

@router.patch("/api/projects/{id}/archive/",response_model=schemas.ProjectResponse,)
@limiter.limit("20/minute")
def toggle_archive(request: Request,id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    project = crud.toggle_archive(db, project)
    return format_project(project)

@router.get("/api/projects/{id}/members/",response_model=List[schemas.ProjectMemberDetail],)
@limiter.limit("60/minute")
def get_project_members(request: Request,id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    if not crud.is_workspace_admin(db, project.workspace_id, current_user.id):
        if not crud.is_project_member(db, id, current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project",)
    members = crud.get_project_members(db, id)
    return [schemas.ProjectMemberDetail(id=m.user.id,username=m.user.username,email=m.user.email,photo=m.user.profile.image_url if m.user.profile else None,
                                        role=m.role,joined_at=m.joined_at,)for m in members]

@router.post("/api/projects/{id}/members/{user_id}/",response_model=schemas.ProjectMemberDetail,)
@limiter.limit("20/minute")
def add_project_member(request: Request,id: int,user_id: int,role: str = Query("viewer", description="Role to assign: viewer, editor, or manager"),
                       db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    if role not in schemas.ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Invalid role. Allowed: {', '.join(sorted(schemas.ALLOWED_ROLES))}",)
    target_user = get_user_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not crud.is_workspace_member(db, project.workspace_id, user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User must be a workspace member before being added to a project",)
    member, created = crud.add_project_member(db, id, user_id, role)
    if not created:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="User is already a member of this project",)
    members = crud.get_project_members(db, id)
    for m in members:
        if m.user_id == user_id:
            return schemas.ProjectMemberDetail(id=m.user.id,username=m.user.username,email=m.user.email,photo=m.user.profile.image_url if m.user.profile else None,
                                               role=m.role,joined_at=m.joined_at,)

@router.delete("/api/projects/{id}/members/{user_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("20/minute")
def remove_project_member(request: Request,id: int,user_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    is_self = current_user.id == user_id
    is_ws_admin = crud.is_workspace_admin(db, project.workspace_id, current_user.id)
    is_manager = crud.get_project_role(db, id, current_user.id) == "manager"

    if not is_self and not is_ws_admin and not is_manager:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only a project manager, workspace admin, or the user themselves can remove a member",)

    target_role = crud.get_project_role(db, id, user_id)
    if target_role == "manager" and crud.count_managers(db, id) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot remove the last manager. Assign another manager first.",)

    success = crud.remove_project_member(db, id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User is not a member of this project",)
    return {"message": "Member removed from project successfully"}

@router.patch("/api/projects/{id}/members/{user_id}/role/",response_model=schemas.ProjectMemberDetail,)
@limiter.limit("20/minute")
def update_member_role(request: Request,id: int,user_id: int,data: schemas.UpdateProjectMemberRole,db: Session = Depends(get_db),
                       current_user: User = Depends(JWTUtil.get_user),):
    project = crud.get_project_or_404(db, id)
    crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    current_role = crud.get_project_role(db, id, user_id)
    if current_role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User is not a member of this project",)
    if current_role == data.role:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"User is already a {data.role}",)
    if (current_role == "manager"and data.role != "manager"and crud.count_managers(db, id) <= 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot demote the last manager. Assign another manager first.",)
    member = crud.update_project_member_role(db, id, user_id, data.role)
    return schemas.ProjectMemberDetail(id=member.user.id,username=member.user.username,email=member.user.email,photo=member.user.profile.image_url if member.user.profile else None,
                                       role=member.role,joined_at=member.joined_at,)