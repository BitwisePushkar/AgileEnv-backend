from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.auth.models import User
from app.project import crud as project_crud
from app.scrum import crud, schemas
from app.scrum.model import ScrumIssue, IssueComment, Sprint, Epic, IssueType
from slowapi import Limiter
from slowapi.util import get_remote_address

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)

def _fmt_user(user) -> Optional[schemas.UserBasic]:
    if not user:
        return None
    return schemas.UserBasic(id=user.id,username=user.username,photo=user.profile.image_url if user.profile else None,)

def _fmt_comment(c: IssueComment) -> schemas.CommentResponse:
    return schemas.CommentResponse(id=c.id,issue_id=c.issue_id,author=_fmt_user(c.author),content=c.content,
                                   is_edited=c.is_edited,created_at=c.created_at,updated_at=c.updated_at,)

def _fmt_issue(issue: ScrumIssue, db: Session) -> schemas.IssueResponse:
    return schemas.IssueResponse(id=issue.id, project_id=issue.project_id, epic_id=issue.epic_id, sprint_id=issue.sprint_id,
                                 parent_id=issue.parent_id, title=issue.title, description=issue.description, type=issue.type.value,
                                 status=issue.status.value, priority=issue.priority.value, story_points=issue.story_points, effective_points=crud.get_effective_points(db, issue),
                                 assignee=_fmt_user(issue.assignee), reporter=_fmt_user(issue.reporter), order=issue.order,
                                 due_date=issue.due_date, completed_at=issue.completed_at, created_at=issue.created_at, updated_at=issue.updated_at,
                                 subtask_count=len(issue.subtasks) if hasattr(issue, "subtasks") and issue.subtasks else 0,
                                 comment_count=len(issue.comments) if hasattr(issue, "comments") and issue.comments else 0,)

def _fmt_issue_detail(issue: ScrumIssue, db: Session) -> schemas.IssueDetailResponse:
    base = _fmt_issue(issue, db)
    return schemas.IssueDetailResponse(**base.model_dump(),subtasks=[_fmt_issue(s, db) for s in (issue.subtasks or [])],
                                       comments=[_fmt_comment(c) for c in (issue.comments or [])],)

def _fmt_epic(epic: Epic, db: Session) -> schemas.EpicResponse:
    return schemas.EpicResponse(id=epic.id, project_id=epic.project_id, title=epic.title, description=epic.description,
                                color=epic.color, status=epic.status.value, start_date=epic.start_date, end_date=epic.end_date,
                                created_by=epic.created_by, created_at=epic.created_at, updated_at=epic.updated_at,
                                issue_count=len(epic.issues) if hasattr(epic, "issues") and epic.issues else 0,)

def _fmt_sprint(sprint: Sprint, db: Session) -> schemas.SprintResponse:
    total_points = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(ScrumIssue.sprint_id == sprint.id,
                                                                                        ScrumIssue.story_points.isnot(None),).scalar() or 0
    issue_count = db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id).count()
    return schemas.SprintResponse(id=sprint.id, project_id=sprint.project_id, name=sprint.name, goal=sprint.goal,
                                  status=sprint.status.value, start_date=sprint.start_date, end_date=sprint.end_date,
                                  completed_at=sprint.completed_at, created_at=sprint.created_at, updated_at=sprint.updated_at,
                                  issue_count=issue_count, total_points=int(total_points),)

def _require_member(db: Session, project_id: int, workspace_id: int, user_id: int):
    if not project_crud.is_workspace_admin(db, workspace_id, user_id):
        if not project_crud.is_project_member(db, project_id, user_id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a member of this project")

@router.post("/api/projects/{project_id}/scrum/epics/",response_model=schemas.EpicResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("30/minute")
def create_epic(request: Request,project_id: int,data: schemas.EpicCreate,db: Session = Depends(get_db),
                current_user: User = Depends(JWTUtil.get_user),):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    epic = crud.create_epic(db, project_id, data, current_user.id)
    return _fmt_epic(epic, db)

@router.get("/api/projects/{project_id}/scrum/epics/",response_model=List[schemas.EpicResponse],)
@limiter.limit("60/minute")
def list_epics(request: Request,project_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    _require_member(db, project_id, project.workspace_id, current_user.id)
    epics = crud.list_epics(db, project_id)
    return [_fmt_epic(e, db) for e in epics]

@router.get("/api/scrum/epics/{epic_id}/",response_model=schemas.EpicDetailResponse,)
@limiter.limit("60/minute")
def get_epic(request: Request,epic_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    epic = crud.get_epic_with_issues(db, epic_id)
    project = project_crud.get_project_or_404(db, epic.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, epic.project_id, project.workspace_id, current_user.id)
    return schemas.EpicDetailResponse(**_fmt_epic(epic, db).model_dump(),issues=[_fmt_issue(i, db) for i in (epic.issues or [])],)

@router.put("/api/scrum/epics/{epic_id}/",response_model=schemas.EpicResponse,)
@limiter.limit("30/minute")
def update_epic(request: Request,epic_id: int,data: schemas.EpicUpdate,db: Session = Depends(get_db),
                current_user: User = Depends(JWTUtil.get_user),):
    epic = crud.get_epic_or_404(db, epic_id)
    project = project_crud.get_project_or_404(db, epic.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    epic = crud.update_epic(db, epic, data)
    return _fmt_epic(epic, db)

@router.delete("/api/scrum/epics/{epic_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("10/minute")
def delete_epic(request: Request,epic_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    epic = crud.get_epic_or_404(db, epic_id)
    project = project_crud.get_project_or_404(db, epic.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    crud.delete_epic(db, epic)
    return {"message": "Epic deleted. Linked issues were not affected."}

@router.patch("/api/scrum/epics/{epic_id}/status/",response_model=schemas.EpicResponse,)
@limiter.limit("30/minute")
def update_epic_status(request: Request,epic_id: int,data: schemas.EpicStatusUpdate,db: Session = Depends(get_db),
                       current_user: User = Depends(JWTUtil.get_user),):
    epic = crud.get_epic_or_404(db, epic_id)
    project = project_crud.get_project_or_404(db, epic.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    epic = crud.update_epic_status(db, epic, data.status)
    return _fmt_epic(epic, db)

@router.post("/api/projects/{project_id}/scrum/sprints/",response_model=schemas.SprintResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("10/minute")
def create_sprint(request: Request,project_id: int,data: schemas.SprintCreate,db: Session = Depends(get_db),
                  current_user: User = Depends(JWTUtil.get_user),):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    sprint = crud.create_sprint(db, project_id, data)
    return _fmt_sprint(sprint, db)

@router.get("/api/projects/{project_id}/scrum/sprints/",response_model=List[schemas.SprintResponse],)
@limiter.limit("60/minute")
def list_sprints(request: Request,project_id: int,db: Session = Depends(get_db),current_user: User = Depends(JWTUtil.get_user),):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    _require_member(db, project_id, project.workspace_id, current_user.id)
    sprints = crud.list_sprints(db, project_id)
    return [_fmt_sprint(s, db) for s in sprints]

@router.get("/api/scrum/sprints/{sprint_id}/",response_model=schemas.SprintDetailResponse,)
@limiter.limit("60/minute")
def get_sprint(request: Request,sprint_id: int,db: Session = Depends(get_db),
               current_user: User = Depends(JWTUtil.get_user),):
    sprint  = crud.get_sprint_with_issues(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, sprint.project_id, project.workspace_id, current_user.id)
    return schemas.SprintDetailResponse(
        **_fmt_sprint(sprint, db).model_dump(),
        issues=[_fmt_issue(i, db) for i in (sprint.issues or [])],
    )

@router.put(
    "/api/scrum/sprints/{sprint_id}/",
    response_model=schemas.SprintResponse,
)
@limiter.limit("20/minute")
def update_sprint(
    request: Request,
    sprint_id: int,
    data: schemas.SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    sprint = crud.update_sprint(db, sprint, data)
    return _fmt_sprint(sprint, db)

@router.delete(
    "/api/scrum/sprints/{sprint_id}/",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
def delete_sprint(
    request: Request,
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    crud.delete_sprint(db, sprint)
    return {"message": "Sprint deleted. Issues moved back to backlog."}

@router.patch(
    "/api/scrum/sprints/{sprint_id}/start/",
    response_model=schemas.SprintResponse,
)
@limiter.limit("5/minute")
def start_sprint(
    request: Request,
    sprint_id: int,
    data: schemas.SprintStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    sprint = crud.start_sprint(db, sprint, data)
    return _fmt_sprint(sprint, db)

@router.patch(
    "/api/scrum/sprints/{sprint_id}/complete/",
    response_model=schemas.SprintResponse,
)
@limiter.limit("5/minute")
def complete_sprint(
    request: Request,
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    sprint = crud.complete_sprint(db, sprint)
    return _fmt_sprint(sprint, db)

@router.post(
    "/api/scrum/sprints/{sprint_id}/issues/{issue_id}/",
    response_model=schemas.IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("60/minute")
def add_issue_to_sprint(
    request: Request,
    sprint_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.get_issue_or_404(db, issue_id)
    issue = crud.add_issue_to_sprint(db, sprint, issue)
    return _fmt_issue(issue, db)

@router.delete(
    "/api/scrum/sprints/{sprint_id}/issues/{issue_id}/",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("60/minute")
def remove_issue_from_sprint(
    request: Request,
    sprint_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.get_issue_or_404(db, issue_id)
    crud.remove_issue_from_sprint(db, sprint, issue)
    return {"message": "Issue removed from sprint and moved to backlog."}

@router.post(
    "/api/projects/{project_id}/scrum/issues/",
    response_model=schemas.IssueDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("60/minute")
def create_issue(
    request: Request,
    project_id: int,
    data: schemas.IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.create_issue(db, project_id, data, current_user.id)
    return _fmt_issue_detail(issue, db)

@router.get(
    "/api/projects/{project_id}/scrum/backlog/",
    response_model=List[schemas.IssueResponse],
)
@limiter.limit("60/minute")
def get_backlog(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    _require_member(db, project_id, project.workspace_id, current_user.id)
    issues = crud.get_backlog(db, project_id)
    return [_fmt_issue(i, db) for i in issues]

@router.get(
    "/api/scrum/issues/{issue_id}/",
    response_model=schemas.IssueDetailResponse,
)
@limiter.limit("60/minute")
def get_issue(
    request: Request,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)
    return _fmt_issue_detail(issue, db)

@router.put(
    "/api/scrum/issues/{issue_id}/",
    response_model=schemas.IssueDetailResponse,
)
@limiter.limit("60/minute")
def update_issue(
    request: Request,
    issue_id: int,
    data: schemas.IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.update_issue(db, issue, data)
    return _fmt_issue_detail(issue, db)


@router.delete(
    "/api/scrum/issues/{issue_id}/",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
def delete_issue(
    request: Request,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="manager")
    crud.delete_issue(db, issue)
    return {"message": "Issue deleted successfully."}

@router.patch(
    "/api/scrum/issues/{issue_id}/status/",
    response_model=schemas.IssueResponse,
)
@limiter.limit("120/minute")
def update_issue_status(
    request: Request,
    issue_id: int,
    data: schemas.IssueStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.update_issue_status(db, issue, data.status)
    return _fmt_issue(issue, db)

@router.patch(
    "/api/scrum/issues/{issue_id}/assign/",
    response_model=schemas.IssueResponse,
)
@limiter.limit("60/minute")
def assign_issue(
    request: Request,
    issue_id: int,
    data: schemas.IssueAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)

    current_role = project_crud.get_project_role(db, issue.project_id, current_user.id)
    is_ws_admin  = project_crud.is_workspace_admin(db, project.workspace_id, current_user.id)

    if not is_ws_admin and current_role == "viewer":
        if data.assignee_id is not None and data.assignee_id != current_user.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Viewers can only assign issues to themselves.",
            )

    issue = crud.assign_issue(db, issue, data.assignee_id)
    return _fmt_issue(issue, db)

@router.patch(
    "/api/scrum/issues/{issue_id}/points/",
    response_model=schemas.IssueResponse,
)
@limiter.limit("60/minute")
def update_story_points(
    request: Request,
    issue_id: int,
    data: schemas.IssuePoints,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.update_story_points(db, issue, data.story_points)
    return _fmt_issue(issue, db)

@router.patch(
    "/api/scrum/issues/{issue_id}/epic/",
    response_model=schemas.IssueResponse,
)
@limiter.limit("30/minute")
def update_issue_epic(
    request: Request,
    issue_id: int,
    data: schemas.IssueEpicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")
    issue = crud.update_issue_epic(db, issue, data.epic_id)
    return _fmt_issue(issue, db)

@router.get(
    "/api/scrum/issues/{issue_id}/subtasks/",
    response_model=List[schemas.IssueResponse],
)
@limiter.limit("60/minute")
def get_subtasks(
    request: Request,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)

    if issue.type != IssueType.STORY:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Only Stories can have subtasks. This issue is type '{issue.type.value}'.",
        )

    subtasks = crud.get_subtasks(db, issue_id)
    return [_fmt_issue(s, db) for s in subtasks]

@router.post(
    "/api/scrum/issues/{issue_id}/comments/",
    response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("60/minute")
def create_comment(
    request: Request,
    issue_id: int,
    data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)
    comment = crud.create_comment(db, issue_id, current_user.id, data)
    return _fmt_comment(comment)

@router.get(
    "/api/scrum/issues/{issue_id}/comments/",
    response_model=List[schemas.CommentResponse],
)
@limiter.limit("60/minute")
def list_comments(
    request: Request,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)
    comments = crud.list_comments(db, issue_id)
    return [_fmt_comment(c) for c in comments]

@router.put(
    "/api/scrum/comments/{comment_id}/",
    response_model=schemas.CommentResponse,
)
@limiter.limit("30/minute")
def update_comment(
    request: Request,
    comment_id: int,
    data: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    comment = crud.get_comment_or_404(db, comment_id)
    issue   = crud.get_issue_or_404(db, comment.issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)
    comment = crud.update_comment(db, comment, current_user.id, data)
    return _fmt_comment(comment)

@router.delete(
    "/api/scrum/comments/{comment_id}/",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
def delete_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    comment = crud.get_comment_or_404(db, comment_id)
    issue   = crud.get_issue_or_404(db, comment.issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)
    requester_role = project_crud.get_project_role(db, issue.project_id, current_user.id) or ""
    crud.delete_comment(db, comment, current_user.id, requester_role)
    return {"message": "Comment deleted successfully."}

@router.get(
    "/api/scrum/comments/{comment_id}/",
    response_model=schemas.CommentResponse,
)
@limiter.limit("60/minute")
def get_comment(
    request: Request,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    comment = crud.get_comment_or_404(db, comment_id)
    issue   = crud.get_issue_or_404(db, comment.issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, issue.project_id, project.workspace_id, current_user.id)
    return _fmt_comment(comment)

@router.get(
    "/api/projects/{project_id}/scrum/board/",
    response_model=schemas.BoardResponse,
)
@limiter.limit("60/minute")
def get_board(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    _require_member(db, project_id, project.workspace_id, current_user.id)

    sprint = crud.get_board(db, project_id)
    if not sprint:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No active sprint found. Start a sprint to view the board.",
        )

    column_statuses = ["todo", "in_progress", "in_review", "done"]
    columns         = []
    total_pts       = 0
    done_pts        = 0

    for col_status in column_statuses:
        col_issues = [
            i for i in sprint.issues
            if i.status.value == col_status and i.parent_id is None
        ]
        pts = sum((crud.get_effective_points(db, i) or 0) for i in col_issues)
        total_pts += pts
        if col_status == "done":
            done_pts = pts

        columns.append(schemas.BoardColumn(
            status=col_status,
            issues=[_fmt_issue(i, db) for i in sorted(col_issues, key=lambda x: x.order)],
            issue_count=len(col_issues),
            total_points=pts,
        ))

    return schemas.BoardResponse(
        project_id=project_id,
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        sprint_goal=sprint.goal,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        total_points=total_pts,
        done_points=done_pts,
        columns=columns,
    )

@router.patch(
    "/api/scrum/issues/{issue_id}/move/",
    response_model=schemas.IssueResponse,
)
@limiter.limit("120/minute")
def move_issue_on_board(
    request: Request,
    issue_id: int,
    data: schemas.IssueStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    issue   = crud.get_issue_or_404(db, issue_id)
    project = project_crud.get_project_or_404(db, issue.project_id)
    crud.assert_scrum_project(project)
    project_crud.require_project_role(db, project, current_user.id, minimum_role="editor")

    if issue.sprint_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Issue is in the backlog. Add it to a sprint before moving on the board.",
        )

    issue = crud.update_issue_status(db, issue, data.status)
    return _fmt_issue(issue, db)

@router.get(
    "/api/projects/{project_id}/scrum/velocity/",
    response_model=schemas.VelocityResponse,
)
@limiter.limit("30/minute")
def get_velocity(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    _require_member(db, project_id, project.workspace_id, current_user.id)

    velocity_data = crud.get_velocity(db, project_id)
    average = (
        sum(v["completed"] for v in velocity_data) / len(velocity_data)
        if velocity_data else 0.0
    )
    return schemas.VelocityResponse(
        project_id=project_id,
        average=round(average, 1),
        sprints=[schemas.VelocityEntry(**v) for v in velocity_data],
    )

@router.get(
    "/api/scrum/sprints/{sprint_id}/burndown/",
    response_model=schemas.BurndownResponse,
)
@limiter.limit("30/minute")
def get_burndown(
    request: Request,
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    sprint  = crud.get_sprint_or_404(db, sprint_id)
    project = project_crud.get_project_or_404(db, sprint.project_id)
    crud.assert_scrum_project(project)
    _require_member(db, sprint.project_id, project.workspace_id, current_user.id)

    if sprint.status.value == "planning":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Burndown is only available for active or completed sprints.",
        )

    total = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(
        ScrumIssue.sprint_id == sprint_id,
        ScrumIssue.story_points.isnot(None),
    ).scalar() or 0

    days = crud.get_burndown(db, sprint)
    return schemas.BurndownResponse(
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        total_points=int(total),
        days=[schemas.BurndownDay(**d) for d in days],
    )

@router.get(
    "/api/projects/{project_id}/scrum/summary/",
    response_model=schemas.ProjectSummary,
)
@limiter.limit("30/minute")
def get_project_summary(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(JWTUtil.get_user),
):
    project = project_crud.get_project_or_404(db, project_id)
    crud.assert_scrum_project(project)
    _require_member(db, project_id, project.workspace_id, current_user.id)

    summary = crud.get_project_summary(db, project_id)
    active_sprint_resp = _fmt_sprint(summary["active_sprint"], db) if summary["active_sprint"] else None

    return schemas.ProjectSummary(
        project_id=project_id,
        total_epics=summary["total_epics"],
        total_sprints=summary["total_sprints"],
        active_sprint=active_sprint_resp,
        open_issues=summary["open_issues"],
        done_issues=summary["done_issues"],
        total_points=summary["total_points"],
        done_points=summary["done_points"],
        average_velocity=summary["average_velocity"],
    )