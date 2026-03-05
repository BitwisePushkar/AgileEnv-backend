import asyncio
import json
import logging
from typing import List, Optional
from fastapi import (APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect,
                     File, Form, UploadFile, status)
from sqlalchemy.orm import Session
from app.auth.models import User
from app.chat import crud, schemas
from app.chat.models import Chatroom, Chattype, Message, PinnedMessage, ChatroomMember, MessageType
from app.workspace.crud import is_workspace_member
from app.utils import JWTUtil
from app.utils.JWTUtil import decode_token
from app.utils.dbUtil import SessionLocal, get_db
from app.utils.S3Util import upload_chat_file
from app.utils.websocketUtil import manager
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
allowed_types = {"text", "image", "file", "audio", "video"}

def _fmt_sender(message: Message) -> schemas.UserBasic:
    sender = message.sender
    profile = getattr(sender, "profile", None)
    return schemas.UserBasic(id = sender.id,
                             username = sender.username,
                             photo = profile.image_url if profile else None,)

def _fmt_reply(message: Message) -> Optional[schemas.ReplyBasic]:
    reply = message.reply_to
    if not reply:
        return None
    sender = reply.sender
    profile = getattr(sender, "profile", None)
    return schemas.ReplyBasic(id = reply.id,
                              sender_id = reply.sender_id,
                              sender_name = (profile.name if profile else None) or sender.username,
                              content = None if reply.deleted else reply.content,
                              message_type = reply.message_type.value,)

def _fmt_forwarded_user(message: "Message") -> "Optional[schemas.UserBasic]":
    user = message.forwarded_from_user
    if not user:
        return None
    profile = getattr(user, "profile", None)
    return schemas.UserBasic(id = user.id,
                             username = user.username,
                             photo = profile.image_url if profile else None,)

def format_message(message: Message) -> schemas.MessageResponse:
    content = None if message.deleted else message.content
    return schemas.MessageResponse(id = message.id,
                                   chat_id = message.chat_id,
                                   sender = _fmt_sender(message),
                                   content = content,
                                   message_type = message.message_type.value,
                                   file_url = None if message.deleted else message.file_url,
                                   file_name = None if message.deleted else message.file_name,
                                   file_size = None if message.deleted else message.file_size,
                                   is_edited = message.is_edited,
                                   deleted = message.deleted,
                                   reply_to = _fmt_reply(message),
                                   is_forwarded = message.is_forwarded,
                                   forwarded_from_user = _fmt_forwarded_user(message),
                                   created_at = message.created_at,
                                   updated_at = message.updated_at,)

def format_chatroom(chatroom: Chatroom) -> schemas.ChatroomResponse:
    members = [schemas.UserBasic(id = u.id,username = u.username,photo = u.profile.image_url 
                                 if getattr(u, "profile", None) else None,) for u in chatroom.members]
    return schemas.ChatroomResponse(id = chatroom.id,
                                    name = chatroom.name,
                                    chat_type = chatroom.chat_type.value,
                                    workspace_id = chatroom.workspace_id,
                                    created_by = chatroom.created_by,
                                    created_at = chatroom.created_at,
                                    updated_at = chatroom.updated_at,
                                    members = members,)

def format_pin(pin: PinnedMessage) -> schemas.PinnedMessageResponse:
    pinner = pin.pinner
    profile = getattr(pinner, "profile", None) if pinner else None
    pinner_basic = (schemas.UserBasic(id = pinner.id,username = pinner.username,photo = profile.image_url 
                                      if profile else None,) if pinner else None)
    return schemas.PinnedMessageResponse(id = pin.id,
                                         chatroom_id = pin.chatroom_id,
                                         message = format_message(pin.message),
                                         pinned_by = pinner_basic,
                                         pinned_at = pin.pinned_at,)

def _get_member_ids(db: Session, chatroom_id: int) -> List[int]:
    rows = db.query(ChatroomMember.user_id).filter(ChatroomMember.chat_id == chatroom_id).all()
    return [r[0] for r in rows]

@router.post("/api/chat/create/",response_model=schemas.ChatroomResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("20/minute")
def create_chatroom(request: Request,data: schemas.ChatroomCreate,current_user: User = Depends(JWTUtil.get_user),
                    db: Session = Depends(get_db),):
    if current_user.id in data.member_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Do not include yourself in member_ids",)
    if data.chat_type == "direct":
        other_id = data.member_ids[0]
        existing = crud.check_direct_chat_exists(db, current_user.id, other_id, data.workspace_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Direct chat already exists between these users")
    if not is_workspace_member(db, data.workspace_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this workspace",)
    for uid in data.member_ids:
        if not is_workspace_member(db, data.workspace_id, uid):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"User {uid} is not a member of this workspace",)
    chatroom = crud.create_chatroom(db, data, current_user.id)
    return format_chatroom(chatroom)

@router.get("/api/chat/list/",response_model=List[schemas.ChatroomResponse],)
@limiter.limit("30/minute")
def list_chatrooms(request: Request,workspace_id: int,current_user: User = Depends(JWTUtil.get_user),
                   db: Session = Depends(get_db),):
    chatrooms = crud.get_user_chatrooms(db, current_user.id, workspace_id)
    return [format_chatroom(c) for c in chatrooms]

@router.get("/api/chat/detail/{chatroom_id}/",response_model=schemas.ChatroomResponse,)
@limiter.limit("30/minute")
def get_chatroom(request: Request,chatroom_id: int,current_user: User = Depends(JWTUtil.get_user),
                 db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this chatroom")
    return format_chatroom(chatroom)

@router.patch("/api/chat/name/{chatroom_id}/",response_model=schemas.ChatroomResponse,)
@limiter.limit("20/minute")
async def rename_chatroom(request: Request,chatroom_id: int,data: schemas.ChatroomUpdate,current_user: User = Depends(JWTUtil.get_user),
                          db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if chatroom.chat_type == Chattype.DIRECT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rename direct chats")
    if chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can rename this chatroom")
    updated = crud.update_chatroom_name(db, chatroom_id, data.name)
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rename failed")
    member_ids = _get_member_ids(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,
                            message = {"type": "chatroom_updated", "data": {"name": data.name}},
                            member_ids = member_ids,)
    return format_chatroom(updated)

@router.patch("/api/chat/transfer/{chatroom_id}/owner/",response_model=schemas.ChatroomResponse,status_code=status.HTTP_200_OK,)
@limiter.limit("10/minute")
async def transfer_ownership(request: Request,chatroom_id: int,data: schemas.TransferOwnership,current_user: User = Depends(JWTUtil.get_user),
                             db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if chatroom.chat_type == Chattype.DIRECT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Direct chats do not have an owner")
    if chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only the current owner can transfer ownership")
    if data.new_owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You are already the owner")
    if not crud.is_member(db, chatroom_id, data.new_owner_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="New owner must already be a member of this chatroom")
    updated = crud.transfer_ownership(db, chatroom_id, data.new_owner_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    member_ids = _get_member_ids(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,message = {"type": "ownership_transferred",
                                                                 "data": {"chatroom_id": chatroom_id,
                                                                          "new_owner_id": data.new_owner_id,
                                                                          "old_owner_id": current_user.id,}},
                                                                          member_ids = member_ids,)
    return format_chatroom(updated)

@router.delete("/api/chat/delete/{chatroom_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("10/minute")
async def delete_chatroom(request: Request,chatroom_id: int,current_user: User = Depends(JWTUtil.get_user),
                          db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if chatroom.chat_type == Chattype.DIRECT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Direct chats cannot be deleted")
    if chatroom.created_by is not None and chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can delete this chatroom")
    member_ids = _get_member_ids(db, chatroom_id)
    crud.delete_chatroom(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,
                            message = {"type": "chatroom_deleted", "data": {"chatroom_id": chatroom_id}},
                            member_ids = member_ids,)
    return {"message": "Chatroom deleted successfully"}

@router.post("/api/chat/{dest_chatroom_id}/messages/forward/",response_model=schemas.MessageResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("30/minute")
async def forward_message(request: Request, dest_chatroom_id: int, data: schemas.ForwardRequest,
                          current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    if not crud.is_member(db, dest_chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of the destination chatroom",)
    message, error = crud.forward_message(db = db,source_message_id = data.source_message_id,
                                          dest_chatroom_id = dest_chatroom_id,
                                          sender_id = current_user.id,caption = data.caption,)
    if error == "source_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail="Source message not found")
    if error == "source_deleted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot forward a deleted message")
    if error == "dest_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,  detail="Destination chatroom not found")
    response = format_message(message)
    member_ids = _get_member_ids(db, dest_chatroom_id)
    await manager.broadcast(chatroom_id = dest_chatroom_id,
                            message = {"type": "new_message", "data": response.model_dump(mode="json")},
                            member_ids = member_ids,)
    return response

@router.get("/api/chat/{chatroom_id}/members/",response_model=List[schemas.ChatroomMemberResponse],)
@limiter.limit("30/minute")
def list_members(request: Request, chatroom_id: int, current_user: User = Depends(JWTUtil.get_user),
                 db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this chatroom")
    members = crud.get_chatroom_members(db, chatroom_id)
    return [schemas.ChatroomMemberResponse(id = m.user.id,
                                           username = m.user.username,
                                           photo = m.user.profile.image_url if getattr(m.user, "profile", None) else None,
                                           joined_at = m.joined_at,) for m in members]

@router.post("/api/chat/{chatroom_id}/member/{user_id}/",status_code=status.HTTP_201_CREATED,)
@limiter.limit("20/minute")
async def add_member(request: Request, chatroom_id: int, user_id: int, current_user: User = Depends(JWTUtil.get_user),
                     db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if not is_workspace_member(db, chatroom.workspace_id, user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User is not a member of the workspace",)
    if chatroom.chat_type == Chattype.DIRECT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add members to direct chats")
    if chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the creator can add members")
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already a member")
    crud.add_member(db, chatroom_id, user_id)
    member_ids = _get_member_ids(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,
                            message = {"type": "member_added", "data": {"user_id": user_id}},
                            member_ids = member_ids,)
    return {"message": "Member added successfully"}

@router.delete("/api/chat/{chatroom_id}/member/{user_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("20/minute")
async def remove_member(request: Request,chatroom_id: int,user_id: int,current_user: User = Depends(JWTUtil.get_user),
                        db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if user_id != current_user.id and chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to remove this member")
    if user_id == chatroom.created_by and user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Creators cannot leave without deleting the chatroom or transferring ownership first.",)
    member_ids = _get_member_ids(db, chatroom_id)
    success = crud.remove_member(db, chatroom_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in chatroom")
    await manager.broadcast(chatroom_id = chatroom_id,
                            message = {"type": "member_removed", "data": {"user_id": user_id}},
                            member_ids = member_ids,)
    return {"message": "Member removed successfully"}

@router.post("/api/chat/{chatroom_id}/messages/",response_model=schemas.MessageResponse,status_code=status.HTTP_201_CREATED,)
@limiter.limit("60/minute")
async def create_message(request: Request,chatroom_id: int,message_type: str = Form("text", description="text | image | file | audio | video"),
                         content: Optional[str] = Form(None, description="Text body or optional caption for file messages"),
                         reply_to_id: Optional[int] = Form(None, description="Parent message ID for threaded replies"),
                         file: Optional[UploadFile] = File(None, description="File to upload — omit for text messages"),
                         current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member of this chatroom",)
    has_content = bool(content and content.strip())
    has_file = file is not None
    if not has_content and not has_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Message must have content, a file, or both",)
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    if has_file:
        file_bytes = await file.read()
        public_url, detected_type = upload_chat_file(content = file_bytes,filename = file.filename or "upload",
                                                     content_type = file.content_type or "application/octet-stream",)
        if public_url is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="File upload failed — check file type and size limits ")
        if detected_type:
            message_type = detected_type
        file_url = public_url
        file_name = file.filename
        file_size = len(file_bytes)
    else:
        message_type = "text"
    if reply_to_id is not None:
        reply_msg = db.query(Message).filter(Message.id == reply_to_id,Message.chat_id == chatroom_id,).first()
        if not reply_msg:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="reply_to_id does not exist in this chatroom",)
        if reply_msg.deleted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot reply to a deleted message",)
    data = schemas.MessageCreate(message_type = message_type,
                                 content = content.strip() if content else None,
                                 file_url = file_url,
                                 file_name = file_name,
                                 file_size = file_size,
                                 reply_to_id = reply_to_id,)
    message = crud.create_message(db, chatroom_id, current_user.id, data)
    response = format_message(message)
    member_ids = _get_member_ids(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,
                            message = {"type": "new_message", "data": response.model_dump(mode="json")},
                            member_ids = member_ids,)
    return response

@router.get("/api/chat/{chatroom_id}/messages/",response_model=List[schemas.MessageResponse],)
@limiter.limit("60/minute")
def get_messages(request: Request,chatroom_id: int,limit: int = Query(50, ge=1, le=100),
                 before_id: Optional[int] = Query(None, description="Cursor — return messages older than this ID"),
                 current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this chatroom")
    messages = crud.get_chat_messages(db, chatroom_id, limit=limit, before_id=before_id)
    return [format_message(m) for m in reversed(messages)]

@router.get("/api/chat/{chatroom_id}/messages/search/",response_model=List[schemas.MessageResponse],)
@limiter.limit("30/minute")
def search_messages(request: Request,chatroom_id: int,q: str = Query(..., min_length=1, max_length=200, description="Search keyword"),
                    limit: int = Query(30, ge=1, le=100),before_id: Optional[int] = Query(None),
                    current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this chatroom")
    messages = crud.search_messages(db, chatroom_id, q, limit=limit, before_id=before_id)
    return [format_message(m) for m in reversed(messages)]

@router.patch("/api/chat/message/{message_id}/",response_model=schemas.MessageResponse,)
@limiter.limit("30/minute")
async def update_message(request: Request,message_id: int,data: schemas.MessageUpdate,
                         current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    message = crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the sender can edit this message")
    if message.deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a deleted message")
    if message.message_type != MessageType.TEXT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only text messages can be edited")
    updated = crud.update_message(db, message_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Edit failed")
    response = format_message(updated)
    member_ids = _get_member_ids(db, message.chat_id)
    await manager.broadcast(chatroom_id = message.chat_id,message = {"type": "message_updated", "data": response.model_dump(mode="json")},
                            member_ids = member_ids,)
    return response

@router.delete("/api/chat/delete/message/{message_id}/",status_code=status.HTTP_200_OK,)
@limiter.limit("20/minute")
async def delete_message(request: Request,message_id: int,current_user: User = Depends(JWTUtil.get_user),
                         db: Session = Depends(get_db),):
    message = crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own messages")
    if message.deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message already deleted")
    deleted = crud.delete_message(db, message_id)
    response = format_message(deleted)
    member_ids = _get_member_ids(db, message.chat_id)
    await manager.broadcast(chatroom_id = message.chat_id,
                            message = {"type": "message_deleted", "data": {"message_id": message_id}},
                            member_ids = member_ids,)
    return {"message": "Message deleted successfully"}

@router.post("/api/chat/{chatroom_id}/messages/{message_id}/pin/",response_model=schemas.PinnedMessageResponse,
             status_code=status.HTTP_201_CREATED,)
@limiter.limit("20/minute")
async def pin_message(request: Request,chatroom_id: int,message_id: int,current_user: User = Depends(JWTUtil.get_user),
                      db: Session = Depends(get_db),):
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this chatroom")
    pin, error = crud.pin_message(db, chatroom_id, message_id, current_user.id)
    if error == "already_pinned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Message is already pinned")
    if error and error.startswith("pin_limit_reached"):
        limit = error.split(":")[1]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Pin limit reached ({limit} max). Unpin a message first.")
    if error == "message_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found in this chatroom")
    if error == "message_deleted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pin a deleted message")
    response = format_pin(pin)
    member_ids = _get_member_ids(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,message = {"type": "message_pinned", "data": response.model_dump(mode="json")},
                            member_ids = member_ids,)
    return response

@router.delete("/api/chat/{chatroom_id}/messages/{message_id}/pin/",status_code=status.HTTP_200_OK,)
@limiter.limit("20/minute")
async def unpin_message(request: Request,chatroom_id: int,message_id: int,current_user: User = Depends(JWTUtil.get_user),
                        db: Session = Depends(get_db),):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this chatroom")
    success, error = crud.unpin_message(db, chatroom_id, message_id, current_user.id, chatroom.created_by)
    if error == "not_pinned":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message is not pinned")
    if error == "forbidden":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the person who pinned it or the creator can unpin")
    member_ids = _get_member_ids(db, chatroom_id)
    await manager.broadcast(chatroom_id = chatroom_id,
                            message = {"type": "message_unpinned", "data": {"message_id": message_id}},
                            member_ids = member_ids,)
    return {"message": "Message unpinned successfully"}

@router.get("/api/chat/{chatroom_id}/pinned/",response_model=List[schemas.PinnedMessageResponse],)
@limiter.limit("30/minute")
def list_pinned_messages(request: Request,chatroom_id: int,current_user: User = Depends(JWTUtil.get_user),
                         db: Session = Depends(get_db),):
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this chatroom")
    pins = crud.get_pinned_messages(db, chatroom_id)
    return [format_pin(p) for p in pins]

@router.post("/api/chat/{chatroom_id}/read/",status_code=status.HTTP_200_OK,)
@limiter.limit("120/minute")
def mark_as_read(request: Request,chatroom_id: int,current_user: User = Depends(JWTUtil.get_user),
                 db: Session = Depends(get_db),):
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this chatroom")
    crud.mark_as_read(db, chatroom_id, current_user.id)
    return {"message": "Messages marked as read"}

@router.get("/api/chat/unread/",response_model=List[schemas.UnreadCountResponse],)
@limiter.limit("60/minute")
def get_unread_counts(request: Request,workspace_id: int,current_user: User = Depends(JWTUtil.get_user),
                      db: Session = Depends(get_db),):
    counts = crud.get_unread_counts(db, current_user.id, workspace_id)
    return counts

@router.websocket("/api/chat/ws/{chatroom_id}/")
async def websocket_endpoint(websocket: WebSocket,chatroom_id: int,token: str = Query(..., description="JWT authentication token"),):
    db = SessionLocal()
    try:
        try:
            payload = decode_token(token)
            user_id = payload.get("user_id") or payload.get("sub")
            current_user = db.query(User).filter(User.id == user_id).first()
            if not current_user:
                raise ValueError("User not found")
        except Exception:
            await websocket.accept()
            await websocket.close(code=4001, reason="Authentication failed")
            return
        if not crud.is_member(db, chatroom_id, current_user.id):
            await websocket.accept()
            await websocket.close(code=4003, reason="Not a member of this chatroom")
            return
        await manager.connect(websocket, current_user.id, chatroom_id)
        heartbeat_task = asyncio.create_task(manager._heartbeat(websocket, current_user.id, chatroom_id))
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    payload_data = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "data": {"detail": "Invalid JSON"}})
                    continue
                msg_type = payload_data.get("type")
                if msg_type == "message":
                    content = (payload_data.get("content") or "").strip()
                    if not content:
                        await websocket.send_json({"type": "error", "data": {"detail": "Empty message"}})
                        continue
                    reply_to_id = payload_data.get("reply_to_id")
                    if reply_to_id is not None:
                        reply_msg = db.query(Message).filter(Message.id == reply_to_id,Message.chat_id == chatroom_id,).first()
                        if not reply_msg or reply_msg.deleted:
                            await websocket.send_json({"type": "error", "data": {"detail": "Invalid reply_to_id"}})
                            continue
                    data = schemas.MessageCreate(content=content, reply_to_id=reply_to_id)
                    message = crud.create_message(db, chatroom_id, current_user.id, data)
                    response = format_message(message)
                    member_ids = _get_member_ids(db, chatroom_id)
                    await manager.broadcast(chatroom_id = chatroom_id,
                                            message = {"type": "new_message", "data": response.model_dump(mode="json")},
                                            member_ids = member_ids,)
                elif msg_type == "pong":
                    pass
                else:
                    await websocket.send_json({"type": "error", "data": {"detail": f"Unknown message type: {msg_type}"}})
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.error("WebSocket error user=%s room=%s: %s", current_user.id, chatroom_id, exc)
        finally:
            heartbeat_task.cancel()
            manager.disconnect(websocket, current_user.id, chatroom_id)
    finally:
        db.close()