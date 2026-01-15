from fastapi import APIRouter,HTTPException,status,WebSocket,WebSocketDisconnect,Request,Query,Depends
from sqlalchemy.orm import Session
from app.chat import schemas
from app.chat import crud
from app.chat.models import Chatroom, Message
from app.auth.models import User
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.utils.JWTUtil import decode_token
from app.utils.websocketUtil import manager
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List
import json

router = APIRouter()
limiter=Limiter(key_func=get_remote_address)

@router.post("/api/chat/create/",response_model=schemas.ChatroomResponse,status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_chatroom(request:Request,data:schemas.ChatroomCreate,current_user:User=Depends(JWTUtil.get_user),
                    db:Session=Depends(get_db)):
    if data.chat_type == "direct":
        other_user_id=data.member_ids[0]
        exist=crud.check_chat_exists(db=db,id=current_user.id,other_id=other_user_id,workspace_id=data.workspace_id)
        if exist:
            return format_chatroom(exist,db)
    chatroom=crud.create_chatroom(db=db,chatroom_data=data,id=current_user.id)
    return format_chatroom(chatroom,db)

@router.get("/api/chat/list/",response_model=List[schemas.ChatroomResponse])
@limiter.limit("20/minute")
def get_user_chats(request:Request,workspace_id:int,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    chatrooms=crud.get_user_chatrooms(db=db,id=current_user.id,workspace_id=workspace_id)
    return [format_chatroom(chat,db) for chat in chatrooms]

@router.get("/api/chat/detail/{id}/",response_model=schemas.ChatroomResponse)
@limiter.limit("20/minute")
def get_detail(request:Request,id:int,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    chatroom=crud.get_chatroom(db,id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Chatroom not found")
    if not crud.is_member(db,id,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not member of this chatroom")
    return format_chatroom(chatroom,db)

@router.put("/api/chat/name/{id}/")
@limiter.limit("20/minute")
async def update_name(request:Request,id:int,name:str=Query(...,min_length=1,max_length=255,description="New chatroom name"),
                               current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    chatroom=crud.get_chatroom(db,id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Chatroom not found")
    if chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only creator can rename")
    update=crud.update_name(db,id,name)
    if not update:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot rename direct chats")
    await manager.broadcast_to_chatroom(chatroom_id=id,message={"type": "chatroom_updated","data": {"name": name}},
                                        db=db)
    return {"message": "Chatroom name updated successfully"}

@router.post("/api/chat/{chatroom_id}/member/{user_id}/")
@limiter.limit("20/minute")
async def add_member(request:Request,chatroom_id: int,user_id: int,current_user:User=Depends(JWTUtil.get_user),
                     db:Session=Depends(get_db)):
    chatroom = crud.get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Chatroom not found")
    if chatroom.chat_type.value == "direct":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot add members to direct chats")
    if not crud.is_member(db, chatroom_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You must be a member to add others")
    crud.add_member(db, chatroom_id, user_id)
    await manager.broadcast_to_chatroom(chatroom_id=chatroom_id,message={"type": "member_added","data": {"user_id": user_id}},
                                        db=db)
    return {"message": "Member added successfully"}

@router.delete("/api/chat/{chatroom_id}/member/{user_id}/")
@limiter.limit("20/minute")
async def remove_member(request:Request,chatroom_id:int,user_id:int,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    chatroom=crud.get_chatroom(db,chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Chatroom not found")
    if user_id != current_user.id and chatroom.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not authorized to remove")
    success=crud.remove_member(db,chatroom_id,user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Member not found in chatroom")
    await manager.broadcast_to_chatroom(chatroom_id=chatroom_id,message={"type": "member_removed","data": {"user_id": user_id}},
                                        db=db)
    return {"message": "Member removed successfully"}

@router.post("/api/chat/{id}/messages/",response_model=schemas.MessageResponse,status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_message(request:Request,id:int,message_data:schemas.Message,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    if not crud.is_member(db,id,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member")
    new_message = crud.create_message(db=db,chatroom_id=id,id=current_user.id,data=message_data)
    response = format_message(new_message, db)
    await manager.broadcast_to_chatroom(chatroom_id=id,message={"type": "new_message","data": response.model_dump()},
                                        db=db)
    return response

@router.get("/api/chat/{chatroom_id}/messages/",response_model=List[schemas.MessageResponse])
@limiter.limit("20/minute")
def get_messages(request:Request,chatroom_id:int,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    if not crud.is_member(db,chatroom_id,current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You are not a member")
    messages=crud.get_chat_messages(db=db,id=chatroom_id)
    return [format_message(msg,db) for msg in reversed(messages)]

@router.put("/api/chat/update/{message_id}/", response_model=schemas.MessageResponse)
@limiter.limit("20/minute")
async def update_message(request:Request,message_id:int,message_data:schemas.Message,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    message=crud.get_message(db,message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Message not found")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Only sender can edit message")
    if message.deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot edit deleted messages")
    updated_message = crud.update_message(db, message_id, message_data)
    response = format_message(updated_message, db)
    await manager.broadcast_to_chatroom(chatroom_id=message.chat_id,message={"type": "message_updated","data": response.model_dump()},
                                        db=db)
    return response

@router.delete("/api/chat/delete/{message_id}/",status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def delete_message(request:Request,message_id:int,current_user:User=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    message = crud.get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Message not found")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You can only delete your own messages")
    crud.delete_message(db, message_id)
    await manager.broadcast_to_chatroom(chatroom_id=message.chat_id,message={"type": "message_deleted","data": {"message_id": message_id}},
                                        db=db)
    return {"message": "Message deleted successfully"}

@router.websocket("/api/chat/ws/{chatroom_id}")
async def websocket_endpoint(websocket: WebSocket,chatroom_id: int,token:str=Query(..., description="JWT authentication token"),db:Session=Depends(get_db)):
    try:
        current_user=await authenticate_websocket(token, db)
    except Exception as e:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    if not crud.is_member(db, chatroom_id, current_user.id):
        await websocket.close(code=4003, reason="Not authorized")
        return
    await manager.connect(websocket, current_user.id, chatroom_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")
            if message_type == "message":
                content = message_data.get("content", "").strip()
                if not content:
                    continue  
                new_message = crud.create_message(db=db,chatroom_id=chatroom_id,id=current_user.id,data=schemas.Message(content=content))
                response = format_message(new_message, db)
                await manager.broadcast_to_chatroom(chatroom_id=chatroom_id,message={"type": "new_message","data": response.model_dump()},db=db)
    except WebSocketDisconnect:
        manager.disconnect(current_user.id, chatroom_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(current_user.id, chatroom_id)

def format_message(message:Message,db:Session)->schemas.MessageResponse:
    sname=message.sender.profile.name if message.sender.profile else message.sender.username
    sphoto = message.sender.profile.image_url if message.sender.profile else None
    return schemas.MessageResponse(id=message.id,chat_id=message.chat_id,sender_id=message.sender_id,name=sname,photo=sphoto,
                                   content=message.content,deleted=message.deleted,created_at=message.created_at,updated_at=message.updated_at)

def format_chatroom(chatroom:Chatroom,db:Session)->schemas.ChatroomResponse:
    return schemas.ChatroomResponse(id=chatroom.id,name=chatroom.name,chat_type=chatroom.chat_type.value,workspace_id=chatroom.workspace_id,
                                    created_by=chatroom.created_by,created_at=chatroom.created_at,updated_at=chatroom.updated_at)

async def authenticate_websocket(token:str,db:Session)->User:
    try:
        payload=decode_token(token)
        user_id=payload.get("user_id") or payload.get("sub")
        user=db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication failed")