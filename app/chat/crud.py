from sqlalchemy.orm import Session,joinedload
from sqlalchemy import desc
from app.chat.models import Chatroom,ChatroomMember,Message,Chattype
from app.auth.models import User
from app.chat.schemas import ChatroomCreate,Message as MessageSchema 
from typing import List,Optional
from datetime import datetime

def get_chatroom(db:Session,id:int)->Optional[Chatroom]:
    return db.query(Chatroom).options(joinedload(Chatroom.members)).filter(Chatroom.id==id).first()

def get_user_chatrooms(db:Session,id:int,workspace_id:int)->List[Chatroom]:
    return db.query(Chatroom).join(ChatroomMember,Chatroom.id==ChatroomMember.chat_id).filter(
        ChatroomMember.user_id == id,Chatroom.workspace_id == workspace_id).options(joinedload(Chatroom.members)).all()
    
def check_chat_exists(db:Session,id:int,other_id: int,workspace_id:int)->Optional[Chatroom]:
    user_chat=db.query(Chatroom).join(ChatroomMember,Chatroom.id == ChatroomMember.chat_id).filter(
        ChatroomMember.user_id == id,Chatroom.chat_type == Chattype.DIRECT,Chatroom.workspace_id == workspace_id).all()
    for chat in user_chat:
        member_ids=[member.id for member in chat.members]
        if other_id in member_ids and len(member_ids) == 2:
            return chat
    return None
    
def create_chatroom(db:Session,chatroom_data:ChatroomCreate,id:int)->Chatroom:
    chatroom=Chatroom(name=chatroom_data.name,chat_type=Chattype(chatroom_data.chat_type),
                          workspace_id=chatroom_data.workspace_id,created_by=id)
    db.add(chatroom)
    db.flush()
    current_user=ChatroomMember(chat_id=chatroom.id,user_id=id)
    db.add(current_user)
    for member_id in chatroom_data.member_ids:
        member=ChatroomMember(chat_id=chatroom.id,user_id=member_id)
        db.add(member)
    db.commit()
    db.refresh(chatroom)
    return chatroom
    
def add_member(db:Session,chatroom_id:int,id:int)->ChatroomMember:
    exist=db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id,ChatroomMember.user_id == id).first()
    if exist:
        return exist
    new=ChatroomMember(chat_id=chatroom_id,user_id=id)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new
    
def remove_member(db:Session,chatroom_id:int,id:int)->bool:
    member=db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id,ChatroomMember.user_id == id).first()
    if member:
        db.delete(member)
        db.commit()
        return True
    return False
    
def is_member(db:Session,chatroom_id:int,id:int)->bool:
    member=db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id,ChatroomMember.user_id == id).first()
    return member is not None
    
def update_name(db:Session,id:int,name:str)->Optional[Chatroom]:
    chatroom=db.query(Chatroom).filter(Chatroom.id == id).first()
    if chatroom and chatroom.chat_type == Chattype.GROUP:
        chatroom.name = name
        db.commit()
        db.refresh(chatroom)
        return chatroom
    return None
    
def delete_chatroom(db:Session,id:int)->bool:
    chatroom=db.query(Chatroom).filter(Chatroom.id == id).first()
    if chatroom:
        db.delete(chatroom)
        db.commit()
        return True
    return False

def get_message(db:Session,id:int)->Optional[Message]:
    return db.query(Message).filter(Message.id == id).first()
    
def get_chat_messages(db:Session,id:int)->List[Message]:
    return db.query(Message).filter(Message.chat_id == id).order_by(desc(Message.created_at)).all()
    
def create_message(db:Session,chatroom_id:int,id:int,data:MessageSchema)->Message:
    message=Message(chat_id=chatroom_id,sender_id=id,content=data.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    db.refresh(message, ['sender'])
    return db.query(Message).options(joinedload(Message.sender).joinedload(User.profile)).filter(Message.id == message.id).first()
    
def update_message(db:Session,id:int,data:MessageSchema)->Optional[Message]:
    message=db.query(Message).filter(Message.id == id).first()
    if message and not message.deleted:
        message.content = data.content
        db.commit()
        return db.query(Message).options(joinedload(Message.sender).joinedload(User.profile)).filter(Message.id == id).first()
    return None
    
def delete_message(db:Session,id:int)->Optional[Message]:
    message=db.query(Message).filter(Message.id == id).first()
    if message:
        message.deleted = True
        db.commit()
        db.refresh(message)
        return message
    return None