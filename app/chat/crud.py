from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.chat.models import Chatroom, ChatroomMember, Message, PinnedMessage, Chattype, MessageType
from app.auth.models import User
from app.chat.schemas import ChatroomCreate, MessageCreate, MessageUpdate
from typing import List, Optional

MAX_PINNED = 5

def _load_message(db: Session, message_id: int) -> Optional[Message]:
    return (db.query(Message).options(joinedload(Message.sender).joinedload(User.profile),joinedload(Message.reply_to).joinedload(Message.sender).joinedload(User.profile),)
            .filter(Message.id == message_id).first())

def get_chatroom(db: Session, chatroom_id: int) -> Optional[Chatroom]:
    return (db.query(Chatroom).options(joinedload(Chatroom.members).joinedload(User.profile))
            .filter(Chatroom.id == chatroom_id).first())

def get_user_chatrooms(db: Session, user_id: int, workspace_id: int) -> List[Chatroom]:
    return (db.query(Chatroom).join(ChatroomMember, Chatroom.id == ChatroomMember.chat_id)
            .filter(ChatroomMember.user_id == user_id, Chatroom.workspace_id == workspace_id)
            .options(joinedload(Chatroom.members).joinedload(User.profile))
            .order_by(desc(Chatroom.last_message_id)).all())

def check_direct_chat_exists(db: Session, user_id: int, other_id: int, workspace_id: int) -> Optional[Chatroom]:
    user_chats = (db.query(Chatroom).join(ChatroomMember, Chatroom.id == ChatroomMember.chat_id)
                  .filter(ChatroomMember.user_id == user_id,Chatroom.chat_type == Chattype.DIRECT,
                          Chatroom.workspace_id == workspace_id,).options(joinedload(Chatroom.members)).all())
    for chat in user_chats:
        member_ids = {m.id for m in chat.members}
        if other_id in member_ids and len(member_ids) == 2:
            return chat
    return None

def create_chatroom(db: Session, data: ChatroomCreate, creator_id: int) -> Chatroom:
    member_ids = [mid for mid in data.member_ids if mid != creator_id]
    chatroom = Chatroom(name = data.name,
                        chat_type = Chattype(data.chat_type),
                        workspace_id = data.workspace_id,
                        created_by = creator_id,)
    db.add(chatroom)
    db.flush() 
    db.add(ChatroomMember(chat_id=chatroom.id, user_id=creator_id))
    seen = set()
    for mid in member_ids:
        if mid not in seen:
            db.add(ChatroomMember(chat_id=chatroom.id, user_id=mid))
            seen.add(mid)
    db.commit()
    db.refresh(chatroom)
    return get_chatroom(db, chatroom.id)

def delete_chatroom(db: Session, chatroom_id: int) -> bool:
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if chatroom:
        db.delete(chatroom)
        db.commit()
        return True
    return False

def update_chatroom_name(db: Session, chatroom_id: int, name: str) -> Optional[Chatroom]:
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if chatroom and chatroom.chat_type == Chattype.GROUP:
        chatroom.name = name
        db.commit()
        db.refresh(chatroom)
        return get_chatroom(db, chatroom_id)
    return None

def is_member(db: Session, chatroom_id: int, user_id: int) -> bool:
    return (db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id, ChatroomMember.user_id == user_id)
            .first()) is not None

def get_chatroom_members(db: Session, chatroom_id: int) -> List[ChatroomMember]:
    return (db.query(ChatroomMember).options(joinedload(ChatroomMember.user).joinedload(User.profile))
            .filter(ChatroomMember.chat_id == chatroom_id).all())

def add_member(db: Session, chatroom_id: int, user_id: int) -> ChatroomMember:
    existing = (db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id, ChatroomMember.user_id == user_id).first())
    if existing:
        return existing
    member = ChatroomMember(chat_id=chatroom_id, user_id=user_id)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def remove_member(db: Session, chatroom_id: int, user_id: int) -> bool:
    member = (db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id, ChatroomMember.user_id == user_id).first())
    if member:
        db.delete(member)
        db.commit()
        return True
    return False

def get_message(db: Session, message_id: int) -> Optional[Message]:
    return _load_message(db, message_id)

def get_chat_messages(db: Session,chatroom_id: int,limit: int = 50,before_id: Optional[int] = None,) -> List[Message]:
    query = (db.query(Message).options(joinedload(Message.sender).joinedload(User.profile),joinedload(Message.reply_to)
                                       .joinedload(Message.sender).joinedload(User.profile),)
                                       .filter(Message.chat_id == chatroom_id))
    if before_id is not None:
        query = query.filter(Message.id < before_id)
    return query.order_by(desc(Message.id)).limit(limit).all()

def create_message(db: Session, chatroom_id: int, sender_id: int, data: MessageCreate) -> Message:
    message = Message(chat_id = chatroom_id,
                      sender_id = sender_id,
                      content = data.content.strip() if data.content else None,
                      message_type = MessageType(data.message_type),
                      file_url = data.file_url,
                      file_name = data.file_name,
                      file_size = data.file_size,
                      reply_to_id = data.reply_to_id,
                      is_edited = False,
                      deleted = False,)
    db.add(message)
    db.flush()
    db.query(Chatroom).filter(Chatroom.id == chatroom_id).update({"last_message_id": message.id},synchronize_session=False,)
    db.commit()
    return _load_message(db, message.id)

def update_message(db: Session, message_id: int, data: MessageUpdate) -> Optional[Message]:
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message or message.deleted:
        return None
    if message.message_type != MessageType.TEXT:
        return None
    message.content   = data.content.strip()
    message.is_edited = True
    db.commit()
    return _load_message(db, message_id)

def delete_message(db: Session, message_id: int) -> Optional[Message]:
    message = db.query(Message).filter(Message.id == message_id).first()
    if message and not message.deleted:
        message.deleted = True
        db.commit()
        return _load_message(db, message_id)
    return None

def forward_message(db: Session,source_message_id: int,dest_chatroom_id: int,sender_id: int,
                    caption: Optional[str] = None,) -> tuple["Message | None", "str | None"]:
    source = _load_message(db, source_message_id)
    if not source:
        return None, "source_not_found"
    if source.deleted:
        return None, "source_deleted"
    dest = db.query(Chatroom).filter(Chatroom.id == dest_chatroom_id).first()
    if not dest:
        return None, "dest_not_found"
    forwarded = Message(chat_id = dest_chatroom_id,
                        sender_id = sender_id,       
                        content = caption or source.content,
                        message_type = source.message_type,
                        file_url = source.file_url,
                        file_name = source.file_name,
                        file_size = source.file_size,
                        is_forwarded = True,
                        forwarded_from_user_id = source.sender_id,
                        is_edited = False,
                        deleted = False,
                        reply_to_id = None,)
    db.add(forwarded)
    db.flush()
    db.query(Chatroom).filter(Chatroom.id == dest_chatroom_id).update({"last_message_id": forwarded.id},synchronize_session=False,)
    db.commit()
    return _load_message(db, forwarded.id), None

def search_messages(db: Session,chatroom_id: int,query: str,limit: int = 30,before_id: Optional[int] = None,) -> List[Message]:
    q = (db.query(Message).options(joinedload(Message.sender).joinedload(User.profile),
                                   joinedload(Message.reply_to).joinedload(Message.sender).joinedload(User.profile),)
                                   .filter(Message.chat_id == chatroom_id,Message.deleted == False,
                                           Message.message_type == MessageType.TEXT,Message.content.ilike(f"%{query.strip()}%"),))
    if before_id is not None:
        q = q.filter(Message.id < before_id)
    return q.order_by(desc(Message.id)).limit(limit).all()

def get_pinned_messages(db: Session, chatroom_id: int) -> List[PinnedMessage]:
    return (db.query(PinnedMessage).options(joinedload(PinnedMessage.message).joinedload(Message.sender).joinedload(User.profile),
                                            joinedload(PinnedMessage.pinner).joinedload(User.profile),)
                                            .filter(PinnedMessage.chatroom_id == chatroom_id)
                                            .order_by(desc(PinnedMessage.pinned_at)).all())

def pin_message(db: Session, chatroom_id: int, message_id: int, pinned_by: int) -> tuple[PinnedMessage | None, str | None]:
    existing = db.query(PinnedMessage).filter(PinnedMessage.chatroom_id == chatroom_id, PinnedMessage.message_id == message_id).first()
    if existing:
        return None, "already_pinned"
    count = db.query(PinnedMessage).filter(PinnedMessage.chatroom_id == chatroom_id).count()
    if count >= MAX_PINNED:
        return None, f"pin_limit_reached:{MAX_PINNED}"
    message = db.query(Message).filter(Message.id == message_id, Message.chat_id == chatroom_id).first()
    if not message:
        return None, "message_not_found"
    if message.deleted:
        return None, "message_deleted"
    pin = PinnedMessage(chatroom_id=chatroom_id, message_id=message_id, pinned_by=pinned_by)
    db.add(pin)
    db.commit()
    db.refresh(pin)
    return (db.query(PinnedMessage).options(joinedload(PinnedMessage.message).joinedload(Message.sender).joinedload(User.profile),
                                            joinedload(PinnedMessage.pinner).joinedload(User.profile),).filter(PinnedMessage.id == pin.id)
                                            .first(),None,)

def unpin_message(db: Session, chatroom_id: int, message_id: int, requesting_user_id: int, chatroom_creator_id: Optional[int]) -> tuple[bool, str | None]:
    pin = (db.query(PinnedMessage).filter(PinnedMessage.chatroom_id == chatroom_id, PinnedMessage.message_id == message_id)
           .first())
    if not pin:
        return False, "not_pinned"
    if pin.pinned_by != requesting_user_id and chatroom_creator_id != requesting_user_id:
        return False, "forbidden"
    db.delete(pin)
    db.commit()
    return True, None

def mark_as_read(db: Session, chatroom_id: int, user_id: int) -> bool:
    latest = (db.query(Message.id).filter(Message.chat_id == chatroom_id)
              .order_by(desc(Message.id)).first())
    if not latest:
        return False
    member = (db.query(ChatroomMember).filter(ChatroomMember.chat_id == chatroom_id, ChatroomMember.user_id == user_id)
              .first())
    if not member:
        return False
    member.last_read_message_id = latest[0]
    db.commit()
    return True

def get_unread_counts(db: Session, user_id: int, workspace_id: int) -> List[dict]:
    memberships = (db.query(ChatroomMember).join(Chatroom, ChatroomMember.chat_id == Chatroom.id)
                   .filter(ChatroomMember.user_id == user_id, Chatroom.workspace_id == workspace_id).all())
    result = []
    for m in memberships:
        q = db.query(Message).filter(Message.chat_id == m.chat_id,Message.deleted == False,)
        if m.last_read_message_id is not None:
            q = q.filter(Message.id > m.last_read_message_id)
        result.append({"chatroom_id": m.chat_id, "unread_count": q.count()})
    return result

def transfer_ownership(db: Session,chatroom_id: int,new_owner_id: int,) -> Optional[Chatroom]:
    chatroom = db.query(Chatroom).filter(Chatroom.id == chatroom_id).first()
    if not chatroom:
        return None
    chatroom.created_by = new_owner_id
    db.commit()
    return get_chatroom(db, chatroom_id)