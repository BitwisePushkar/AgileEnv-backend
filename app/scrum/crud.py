from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status as http_status
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from app.scrum.model import (Epic, Sprint, ScrumIssue, IssueComment, EpicStatus, SprintStatus, IssueType,
                             IssueStatus, IssuePriority,)
from app.scrum import schemas
from app.project.model import Project
from app.project.crud import is_project_member
from app.auth.models import User

ORDER_STEP = 1000.0 

def assert_scrum_project(project: Project) -> None:
    if project.board_type.value != "scrum":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail=f"This project uses {project.board_type.value.title()}, not Scrum",)

def _next_backlog_order(db: Session, project_id: int) -> float:
    max_val = db.query(func.max(ScrumIssue.order)).filter(ScrumIssue.project_id == project_id,
                                                          ScrumIssue.sprint_id.is_(None),).scalar()
    return (max_val or 0) + ORDER_STEP

def _next_sprint_order(db: Session, sprint_id: int) -> float:
    max_val = db.query(func.max(ScrumIssue.order)).filter(ScrumIssue.sprint_id == sprint_id,).scalar()
    return (max_val or 0) + ORDER_STEP

def get_epic_or_404(db: Session, epic_id: int) -> Epic:
    epic = db.get(Epic, epic_id)
    if not epic:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Epic not found")
    return epic

def get_sprint_or_404(db: Session, sprint_id: int) -> Sprint:
    sprint = db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint

def get_issue_or_404(db: Session, issue_id: int) -> ScrumIssue:
    issue = (db.query(ScrumIssue).options(
        joinedload(ScrumIssue.assignee).joinedload(User.profile),
        joinedload(ScrumIssue.reporter).joinedload(User.profile),
        joinedload(ScrumIssue.subtasks).joinedload(ScrumIssue.assignee).joinedload(User.profile),
        joinedload(ScrumIssue.comments).joinedload(IssueComment.author).joinedload(User.profile),
        joinedload(ScrumIssue.epic),
        joinedload(ScrumIssue.sprint),).filter(ScrumIssue.id == issue_id).first())
    if not issue:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Issue not found")
    return issue

def get_comment_or_404(db: Session, comment_id: int) -> IssueComment:
    comment = (db.query(IssueComment).options(joinedload(IssueComment.author).joinedload(User.profile))
               .filter(IssueComment.id == comment_id).first())
    if not comment:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Comment not found")
    return comment

def get_effective_points(db: Session, issue: ScrumIssue) -> Optional[int]:
    if issue.type == IssueType.STORY:
        total = db.query(func.sum(ScrumIssue.story_points)).filter(ScrumIssue.parent_id == issue.id,ScrumIssue.story_points.isnot(None),
                                                                   ).scalar()
        if total is not None:
            return int(total)
    return issue.story_points

def create_epic(db: Session, project_id: int, data: schemas.EpicCreate, creator_id: int) -> Epic:
    epic = Epic(project_id=project_id,title=data.title,description=data.description,color=data.color,
                start_date=data.start_date,end_date=data.end_date,created_by=creator_id,)
    db.add(epic)
    db.commit()
    db.refresh(epic)
    return epic

def list_epics(db: Session, project_id: int) -> List[Epic]:
    return (db.query(Epic).filter(Epic.project_id == project_id).order_by(Epic.created_at.desc()).all())

def get_epic_with_issues(db: Session, epic_id: int) -> Epic:
    epic = (db.query(Epic).options(joinedload(Epic.issues).joinedload(ScrumIssue.assignee).joinedload(User.profile),)
            .filter(Epic.id == epic_id).first())
    if not epic:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Epic not found")
    return epic

def update_epic(db: Session, epic: Epic, data: schemas.EpicUpdate) -> Epic:
    updates = data.model_dump(exclude_unset=True)
    new_start = updates.get("start_date", epic.start_date)
    new_end = updates.get("end_date",   epic.end_date)
    if new_start and new_end and new_end <= new_start:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "end_date must be after start_date")
    for field, value in updates.items():
        setattr(epic, field, value)
    db.commit()
    db.refresh(epic)
    return epic

def update_epic_status(db: Session, epic: Epic, new_status: str) -> Epic:
    epic.status = EpicStatus(new_status)
    db.commit()
    db.refresh(epic)
    return epic

def delete_epic(db: Session, epic: Epic) -> None:
    db.delete(epic)
    db.commit()

def create_sprint(db: Session, project_id: int, data: schemas.SprintCreate) -> Sprint:
    sprint = Sprint(project_id=project_id,name=data.name,goal=data.goal,)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint

def list_sprints(db: Session, project_id: int) -> List[Sprint]:
    return (db.query(Sprint).filter(Sprint.project_id == project_id).order_by(Sprint.created_at.desc()).all())

def get_sprint_with_issues(db: Session, sprint_id: int) -> Sprint:
    sprint = (db.query(Sprint).options(joinedload(Sprint.issues).joinedload(ScrumIssue.assignee).joinedload(User.profile),)
              .filter(Sprint.id == sprint_id).first())
    if not sprint:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint

def update_sprint(db: Session, sprint: Sprint, data: schemas.SprintUpdate) -> Sprint:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    return sprint

def start_sprint(db: Session, sprint: Sprint, data: schemas.SprintStart) -> Sprint:
    if sprint.status != SprintStatus.PLANNING:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST," Only 'planning' sprints can be started.",)
    active = db.query(Sprint).filter(Sprint.project_id == sprint.project_id,Sprint.status == SprintStatus.ACTIVE,).first()
    if active:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Sprint '{active.name}' is already active. Complete it before starting a new one.",)
    issue_count = db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id).count()
    if issue_count == 0:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot start an empty sprint. Add at least one issue first.",)
    sprint.status = SprintStatus.ACTIVE
    sprint.start_date = data.start_date
    sprint.end_date = data.end_date
    db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status == IssueStatus.BACKLOG,).update({"status": IssueStatus.TODO})
    db.commit()
    db.refresh(sprint)
    return sprint

def complete_sprint(db: Session, sprint: Sprint) -> Sprint:
    if sprint.status != SprintStatus.ACTIVE:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Only 'active' sprints can be completed.",)
    unfinished = db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status != IssueStatus.DONE,).all()
    for issue in unfinished:
        issue.sprint_id = None
        issue.status = IssueStatus.BACKLOG
    sprint.status = SprintStatus.COMPLETED
    sprint.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sprint)
    return sprint

def delete_sprint(db: Session, sprint: Sprint) -> None:
    if sprint.status != SprintStatus.PLANNING:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Only 'planning' sprints can be deleted.",)
    db.query(ScrumIssue).filter(ScrumIssue.sprint_id == sprint.id).update({"sprint_id": None, "status": IssueStatus.BACKLOG})
    db.delete(sprint)
    db.commit()

def add_issue_to_sprint(db: Session, sprint: Sprint, issue: ScrumIssue) -> ScrumIssue:
    if sprint.status == SprintStatus.COMPLETED:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Cannot add issues to a completed sprint.")
    if issue.project_id != sprint.project_id:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Issue does not belong to this project.")
    if issue.type == IssueType.SUBTASK:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"SubTasks cannot be added directly to a sprint. Add the parent Story instead.",)
    if issue.sprint_id is not None:
        if issue.sprint_id == sprint.id:
            raise HTTPException(http_status.HTTP_409_CONFLICT, "Issue is already in this sprint.")
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Issue is already in another sprint (id={issue.sprint_id}). Remove it first.",)
    issue.sprint_id = sprint.id
    if sprint.status == SprintStatus.ACTIVE:
        issue.status = IssueStatus.TODO
    if issue.type == IssueType.STORY:
        subtasks = db.query(ScrumIssue).filter(ScrumIssue.parent_id == issue.id).all()
        for subtask in subtasks:
            subtask.sprint_id = sprint.id
            if sprint.status == SprintStatus.ACTIVE:
                subtask.status = IssueStatus.TODO
    db.commit()
    return get_issue_or_404(db, issue.id)

def remove_issue_from_sprint(db: Session, sprint: Sprint, issue: ScrumIssue) -> None:
    if sprint.status == SprintStatus.COMPLETED:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Cannot remove issues from a completed sprint.")
    if issue.sprint_id != sprint.id:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Issue is not in this sprint.")
    issue.sprint_id = None
    issue.status = IssueStatus.BACKLOG
    if issue.type == IssueType.STORY:
        subtasks = db.query(ScrumIssue).filter(ScrumIssue.parent_id == issue.id).all()
        for subtask in subtasks:
            subtask.sprint_id = None
            subtask.status = IssueStatus.BACKLOG
    db.commit()

def create_issue(db: Session,project_id: int,data: schemas.IssueCreate,reporter_id: int,) -> ScrumIssue:
    if data.type == "subtask":
        parent = db.get(ScrumIssue, data.parent_id)
        if not parent:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Parent issue not found.")
        if parent.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Parent issue does not belong to this project.")
        if parent.type != IssueType.STORY:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"SubTasks can only be children of a Story. Parent is type '{parent.type.value}'.",)
    if data.epic_id:
        epic = db.get(Epic, data.epic_id)
        if not epic or epic.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Epic not found or does not belong to this project.")
    sprint_id = None
    initial_status = IssueStatus.BACKLOG
    if data.sprint_id:
        sprint = db.get(Sprint, data.sprint_id)
        if not sprint or sprint.project_id != project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Sprint not found or does not belong to this project.")
        if sprint.status == SprintStatus.COMPLETED:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Cannot add issues to a completed sprint.")
        sprint_id = data.sprint_id
        initial_status = IssueStatus.TODO if sprint.status == SprintStatus.ACTIVE else IssueStatus.BACKLOG
    if data.assignee_id and not is_project_member(db, project_id, data.assignee_id):
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Assignee must be a member of this project.")
    order = _next_sprint_order(db, sprint_id) if sprint_id else _next_backlog_order(db, project_id)
    issue = ScrumIssue(project_id=project_id,epic_id=data.epic_id,sprint_id=sprint_id,parent_id=data.parent_id,
                       title=data.title,description=data.description,type=IssueType(data.type),status=initial_status,
                       priority=IssuePriority(data.priority or "medium"),story_points=data.story_points,assignee_id=data.assignee_id,
                       reporter_id=reporter_id,order=order,due_date=data.due_date,)
    db.add(issue)
    db.commit()
    return get_issue_or_404(db, issue.id)

def get_backlog(db: Session, project_id: int) -> List[ScrumIssue]:
    return (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee).joinedload(User.profile),joinedload(ScrumIssue.reporter).joinedload(User.profile),
                                         joinedload(ScrumIssue.subtasks),joinedload(ScrumIssue.epic),)
                                         .filter(ScrumIssue.project_id == project_id,ScrumIssue.sprint_id.is_(None),
                                                 ScrumIssue.parent_id.is_(None),).order_by(ScrumIssue.order).all())

def update_issue(db: Session, issue: ScrumIssue, data: schemas.IssueUpdate) -> ScrumIssue:
    updates = data.model_dump(exclude_unset=True)

    if "epic_id" in updates and updates["epic_id"] is not None:
        epic = db.get(Epic, updates["epic_id"])
        if not epic or epic.project_id != issue.project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Epic not found or does not belong to this project.")
    if "assignee_id" in updates and updates["assignee_id"] is not None:
        if not is_project_member(db, issue.project_id, updates["assignee_id"]):
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Assignee must be a member of this project.")
    if "priority" in updates and updates["priority"] is not None:
        updates["priority"] = IssuePriority(updates["priority"])
    for field, value in updates.items():
        setattr(issue, field, value)
    db.commit()
    return get_issue_or_404(db, issue.id)

def update_issue_status(db: Session, issue: ScrumIssue, new_status: str) -> ScrumIssue:
    current = issue.status.value
    allowed = schemas.STATUS_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST,f"Cannot transition from '{current}' to '{new_status}'. "
                            f"Allowed next statuses: {sorted(allowed)}",)
    issue.status = IssueStatus(new_status)
    if new_status == "done":
        issue.completed_at = datetime.now(timezone.utc)
    elif current == "done" and new_status == "in_progress":
        issue.completed_at = None 
    db.commit()
    return get_issue_or_404(db, issue.id)

def assign_issue(db: Session, issue: ScrumIssue, assignee_id: Optional[int]) -> ScrumIssue:
    if assignee_id is not None and not is_project_member(db, issue.project_id, assignee_id):
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Assignee must be a member of this project.")
    issue.assignee_id = assignee_id
    db.commit()
    return get_issue_or_404(db, issue.id)

def update_story_points(db: Session, issue: ScrumIssue, points: int) -> ScrumIssue:
    issue.story_points = points
    db.commit()
    return get_issue_or_404(db, issue.id)

def update_issue_epic(db: Session, issue: ScrumIssue, epic_id: Optional[int]) -> ScrumIssue:
    if epic_id is not None:
        epic = db.get(Epic, epic_id)
        if not epic or epic.project_id != issue.project_id:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Epic not found or does not belong to this project.")
    issue.epic_id = epic_id
    db.commit()
    return get_issue_or_404(db, issue.id)

def get_subtasks(db: Session, issue_id: int) -> List[ScrumIssue]:
    return (db.query(ScrumIssue).options(joinedload(ScrumIssue.assignee).joinedload(User.profile),joinedload(ScrumIssue.reporter).joinedload(User.profile),)
            .filter(ScrumIssue.parent_id == issue_id).order_by(ScrumIssue.order).all())

def delete_issue(db: Session, issue: ScrumIssue) -> None:
    if issue.sprint_id is not None:
        sprint = db.get(Sprint, issue.sprint_id)
        if sprint and sprint.status == SprintStatus.ACTIVE:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST,"Cannot delete an issue in an active sprint. Remove it from the sprint first.",)
    db.delete(issue)
    db.commit()

def create_comment(db: Session, issue_id: int, author_id: int, data: schemas.CommentCreate) -> IssueComment:
    comment = IssueComment(issue_id=issue_id, author_id=author_id, content=data.content)
    db.add(comment)
    db.commit()
    return get_comment_or_404(db, comment.id)

def list_comments(db: Session, issue_id: int) -> List[IssueComment]:
    return (db.query(IssueComment).options(joinedload(IssueComment.author).joinedload(User.profile))
            .filter(IssueComment.issue_id == issue_id).order_by(IssueComment.created_at).all())

def update_comment(db: Session, comment: IssueComment, author_id: int, data: schemas.CommentUpdate) -> IssueComment:
    if comment.author_id != author_id:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, "Only the comment author can edit this comment.")
    comment.content   = data.content
    comment.is_edited = True
    db.commit()
    return get_comment_or_404(db, comment.id)

def delete_comment(db: Session, comment: IssueComment, requester_id: int, requester_role: str) -> None:
    is_author = comment.author_id == requester_id
    is_manager = requester_role == "manager"
    if not is_author and not is_manager:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN,"Only the comment author or a project manager can delete this comment.",)
    db.delete(comment)
    db.commit()

def get_active_sprint(db: Session, project_id: int) -> Optional[Sprint]:
    return db.query(Sprint).filter(Sprint.project_id == project_id,Sprint.status == SprintStatus.ACTIVE,).first()

def get_board(db: Session, project_id: int) -> Optional[Sprint]:
    return (db.query(Sprint).options(joinedload(Sprint.issues).joinedload(ScrumIssue.assignee).joinedload(User.profile),)
            .filter(Sprint.project_id == project_id,Sprint.status == SprintStatus.ACTIVE,).first())

def get_velocity(db: Session, project_id: int) -> List[dict]:
    sprints = db.query(Sprint).filter(Sprint.project_id == project_id,Sprint.status == SprintStatus.COMPLETED,
                                      ).order_by(Sprint.completed_at).all()
    result = []
    for sprint in sprints:
        committed = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.story_points.isnot(None),
                                                                                         ).scalar() or 0
        completed = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(ScrumIssue.sprint_id == sprint.id,
                                                                                         ScrumIssue.status == IssueStatus.DONE,ScrumIssue.story_points.isnot(None),).scalar() or 0
        result.append({"sprint_id": sprint.id,"sprint_name": sprint.name,"committed": int(committed),
                       "completed": int(completed),})
    return result

def get_burndown(db: Session, sprint: Sprint) -> List[dict]:
    if not sprint.start_date:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Sprint has not been started yet.")
    total = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(ScrumIssue.sprint_id == sprint.id,
                                                                                 ScrumIssue.story_points.isnot(None),).scalar() or 0
    total = int(total)
    done_issues = db.query(ScrumIssue.completed_at, ScrumIssue.story_points).filter(ScrumIssue.sprint_id == sprint.id,ScrumIssue.status == IssueStatus.DONE,
                                                                                    ScrumIssue.completed_at.isnot(None),ScrumIssue.story_points.isnot(None),).all()
    today = datetime.now(timezone.utc)
    chart_end = min(sprint.end_date or today, today)
    total_days = max((sprint.end_date.date() - sprint.start_date.date()).days, 1) if sprint.end_date else 1
    days = []
    current = sprint.start_date.date()
    while current <= chart_end.date():
        done_so_far = sum((pts or 0)for completed_at, pts in done_issues if completed_at and completed_at.date() <= current)
        days_elapsed = (current - sprint.start_date.date()).days
        ideal = total * (1 - days_elapsed / total_days)
        days.append({"date": current.isoformat(),"remaining": max(total - done_so_far, 0),"ideal": round(ideal, 2),})
        current += timedelta(days=1)
    return days

def get_project_summary(db: Session, project_id: int) -> dict:
    total_epics = db.query(Epic).filter(Epic.project_id == project_id).count()
    total_sprints = db.query(Sprint).filter(Sprint.project_id == project_id).count()
    active_sprint = get_active_sprint(db, project_id)
    open_issues = db.query(ScrumIssue).filter(ScrumIssue.project_id == project_id,ScrumIssue.status != IssueStatus.DONE,
                                              ScrumIssue.parent_id.is_(None),).count()
    done_issues = db.query(ScrumIssue).filter(ScrumIssue.project_id == project_id,ScrumIssue.status == IssueStatus.DONE,
                                              ScrumIssue.parent_id.is_(None),).count()
    total_points = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(ScrumIssue.project_id == project_id,
                                                                                        ScrumIssue.story_points.isnot(None),).scalar() or 0
    done_points = db.query(func.coalesce(func.sum(ScrumIssue.story_points), 0)).filter(ScrumIssue.project_id == project_id,ScrumIssue.status == IssueStatus.DONE,
                                                                                       ScrumIssue.story_points.isnot(None),).scalar() or 0
    velocity_data = get_velocity(db, project_id)
    avg_velocity  = (sum(v["completed"] for v in velocity_data) / len(velocity_data) if velocity_data else 0.0)
    return {"project_id": project_id,"total_epics": total_epics,"total_sprints": total_sprints,"active_sprint": active_sprint,
            "open_issues": open_issues,"done_issues": done_issues,"total_points": int(total_points),"done_points": int(done_points),
            "average_velocity": round(avg_velocity, 1),}