from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from typing import Optional, List
from app.project.model import Project, ProjectMember, BoardType
from app.workspace.model import WorkspaceMember
from app.auth.models import User, Profile
from app.project import schemas
ROLE_RANK = {"viewer": 1, "editor": 2, "manager": 3}

def get_project_or_404(db: Session, project_id: int) -> Project:
    project = (db.query(Project).options(joinedload(Project.members).joinedload(ProjectMember.user).joinedload(User.profile))
               .filter(Project.id == project_id).first())
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

def is_workspace_member(db: Session, workspace_id: int, user_id: int) -> bool:
    return db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id,WorkspaceMember.user_id == user_id,
                                            ).first() is not None

def is_workspace_admin(db: Session, workspace_id: int, user_id: int) -> bool:
    member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id,WorkspaceMember.user_id == user_id,).first()
    return member is not None and member.role == "admin"

def get_project_member(db: Session, project_id: int, user_id: int) -> Optional[ProjectMember]:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id,ProjectMember.user_id == user_id,).first()

def is_project_member(db: Session, project_id: int, user_id: int) -> bool:
    return get_project_member(db, project_id, user_id) is not None

def get_project_role(db: Session, project_id: int, user_id: int) -> Optional[str]:
    member = get_project_member(db, project_id, user_id)
    return member.role if member else None

def require_project_role(db: Session,project: Project,user_id: int,minimum_role: str,):
    if is_workspace_admin(db, project.workspace_id, user_id):
        return
    member = get_project_member(db, project.id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this project",)
    if ROLE_RANK.get(member.role, 0) < ROLE_RANK.get(minimum_role, 99):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"This action requires '{minimum_role}' role or higher",)

def create_project(db: Session,workspace_id: int,data: schemas.ProjectCreate,creator_id: int,) -> Project:
    project = Project(workspace_id=workspace_id,name=data.name,description=data.description,icon=data.icon,
                      color=data.color,board_type=BoardType(data.board_type),created_by=creator_id,)
    db.add(project)
    db.flush() 
    creator_member = ProjectMember(project_id=project.id,user_id=creator_id,role="manager",)
    db.add(creator_member)
    db.commit()
    db.refresh(project)
    return project

def list_projects(db: Session,workspace_id: int,user_id: int,include_archived: bool = False,) -> List[Project]:
    query = db.query(Project).filter(Project.workspace_id == workspace_id)
    if not include_archived:
        query = query.filter(Project.is_archived == False)
    if not is_workspace_admin(db, workspace_id, user_id):
        query = query.join(ProjectMember).filter(ProjectMember.user_id == user_id)
    return query.order_by(Project.created_at.desc()).all()

def update_project(db: Session,project: Project,data: schemas.ProjectUpdate,) -> Project:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()

def toggle_archive(db: Session, project: Project) -> Project:
    project.is_archived = not project.is_archived
    db.commit()
    db.refresh(project)
    return project

def get_project_members(db: Session, project_id: int) -> List[ProjectMember]:
    return (db.query(ProjectMember).options(joinedload(ProjectMember.user).joinedload(User.profile))
            .filter(ProjectMember.project_id == project_id).all())

def add_project_member(db: Session,project_id: int,user_id: int,role: str = "viewer",) -> ProjectMember:
    existing = get_project_member(db, project_id, user_id)
    if existing:
        return existing , False
    member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member , True

def remove_project_member(db: Session, project_id: int, user_id: int) -> bool:
    member = get_project_member(db, project_id, user_id)
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True

def update_project_member_role(db: Session,project_id: int,user_id: int,new_role: str,) -> ProjectMember:
    member = get_project_member(db, project_id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User is not a member of this project",)
    member.role = new_role
    db.commit()
    db.refresh(member)
    return member

def count_managers(db: Session, project_id: int) -> int:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id,ProjectMember.role == "manager",).count()