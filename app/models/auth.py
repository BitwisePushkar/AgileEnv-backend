from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,Float,Boolean

Base=declarative_base()

class User(Base):

    __tablename__="users"

    id = Column(Integer,primary_key=True,index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_active=Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
