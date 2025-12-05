from sqlalchemy import Table,Column,Integer,String,DateTime,MetaData,Sequence

metadata=MetaData()

users=Table(
    "users",metadata,
    Column("Id",Integer,Sequence("user_id_seq"),primary_key=True),
    Column("Email",String(100)),
    Column("Password",String(100)),
    Column("UserName",String(50)),
    Column("created_at",DateTime),
    Column("status",String(1))
)