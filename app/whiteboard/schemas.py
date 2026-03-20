from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

class ElementType(str, Enum):
    PATH = "path"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    STICKY_NOTE = "sticky_note"
    IMAGE = "image"

class ActionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    MOVE = "move"
    RESIZE = "resize"
    DELETE = "delete"
    UNDO = "undo"

class UserMini(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    model_config = {"from_attributes": True}

class WhiteboardOut(BaseModel):
    id: int
    project_id: int
    title: str
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class WhiteboardUpdate(BaseModel):
    title: Optional[str]  = Field(None, max_length=255)
    is_locked: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one(self) -> "WhiteboardUpdate":
        if self.title is None and self.is_locked is None:
            raise ValueError("Provide at least one field to update.")
        return self

class WhiteboardElementCreate(BaseModel):
    element_type: ElementType
    data: Dict[str, Any] = Field(..., description="Type-specific geometry + style JSON")
    z_index: int = Field(default=0, ge=0)

    @field_validator("data")
    @classmethod
    def data_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("Element data cannot be empty.")
        return v

class WhiteboardElementUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    z_index: Optional[int] = Field(None, ge=0)
    is_locked: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one(self) -> "WhiteboardElementUpdate":
        if self.data is None and self.z_index is None and self.is_locked is None:
            raise ValueError("Provide at least one field to update.")
        return self

class WhiteboardElementOut(BaseModel):
    id: int
    whiteboard_id: int
    element_type: ElementType
    data: Dict[str, Any]
    z_index: int
    is_locked: bool
    is_deleted: bool
    created_by: int
    created_by_user: Optional[UserMini] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class ElementsBulkOut(BaseModel):
    whiteboard_id: int
    elements: List[WhiteboardElementOut]
    total: int

class HistoryDelta(BaseModel):
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None

class WhiteboardHistoryOut(BaseModel):
    id: int
    whiteboard_id: int
    element_id: Optional[int]
    action_type: ActionType
    delta: Dict[str, Any]
    performed_by: int
    performed_by_user: Optional[UserMini] = None
    performed_at: datetime
    model_config = {"from_attributes": True}

class WhiteboardHistoryListOut(BaseModel):
    whiteboard_id: int
    entries: List[WhiteboardHistoryOut]
    total: int

class ActiveUser(BaseModel):
    user: UserMini
    cursor_x: Optional[float] = None
    cursor_y: Optional[float] = None

class ActiveUsersOut(BaseModel):
    whiteboard_id: int
    active_users: List[ActiveUser]
    count: int

class WS_Ping(BaseModel):
    type: Literal["ping"]

class WS_CursorMove(BaseModel):
    type: Literal["cursor_move"]
    x: float
    y: float

class WS_DrawStart(BaseModel):
    type: Literal["draw_start"]
    temp_id: str
    element_type: ElementType
    data: Dict[str, Any]
    z_index: int = 0

class WS_DrawDelta(BaseModel):
    type: Literal["draw_delta"]
    temp_id: str
    points: List[List[float]] = Field(..., description="[[x,y], ...] chunk")

class WS_DrawEnd(BaseModel):
    type: Literal["draw_end"]
    element_id: int
    temp_id: str
    data: Dict[str, Any]

class WS_ElementUpdate(BaseModel):
    type: Literal["element_update"]
    element_id: int
    data: Dict[str, Any]

class WS_ElementMove(BaseModel):
    type: Literal["element_move"]
    element_id: int
    dx: float
    dy: float

class WS_ElementResize(BaseModel):
    type: Literal["element_resize"]
    element_id: int
    data: Dict[str, Any]

class WS_ElementDelete(BaseModel):
    type: Literal["element_delete"]
    element_id: int

class WS_Undo(BaseModel):
    type: Literal["undo"]

WS_InboundMessage = Union[ WS_Ping, WS_CursorMove, WS_DrawStart, WS_DrawDelta, WS_DrawEnd, WS_ElementUpdate,
                          WS_ElementMove, WS_ElementResize, WS_ElementDelete, WS_Undo,]

class WS_Pong(BaseModel):
    type: Literal["pong"] = "pong"

class WS_InitPayload(BaseModel):
    type: Literal["init"] = "init"
    whiteboard: WhiteboardOut
    elements: List[WhiteboardElementOut]
    active_users: List[ActiveUser]
    cursors: List[dict]  

class WS_ElementCreated(BaseModel):
    type: Literal["element_created"] = "element_created"
    temp_id: Optional[str] = None
    element: WhiteboardElementOut

class WS_ElementUpdated(BaseModel):
    type: Literal["element_updated"] = "element_updated"
    element: WhiteboardElementOut

class WS_ElementDeleted(BaseModel):
    type: Literal["element_deleted"] = "element_deleted"
    element_id: int
    deleted_by: int

class WS_CursorBroadcast(BaseModel):
    type: Literal["cursor"] = "cursor"
    user_id: int
    x: float
    y: float

class WS_DrawDeltaBroadcast(BaseModel):
    type: Literal["draw_delta_broadcast"] = "draw_delta_broadcast"
    user_id: int
    temp_id: str
    points: List[List[float]]

class WS_UserJoined(BaseModel):
    type: Literal["user_joined"] = "user_joined"
    user: UserMini

class WS_UserLeft(BaseModel):
    type: Literal["user_left"] = "user_left"
    user_id: int

class WS_UndoResult(BaseModel):
    type: Literal["undo_result"] = "undo_result"
    user_id: int
    element: Optional[WhiteboardElementOut] = None

class WS_BoardLocked(BaseModel):
    type: Literal["board_locked"] = "board_locked"
    is_locked: bool
    by_user: int

class WS_Error(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str