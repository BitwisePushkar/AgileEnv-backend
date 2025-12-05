import databases
from sqlalchemy import create_engine
from functools import lru_cache          #least recently used 
from app import config
from app.models import metadata

@lru_cache()
def setting():
    return config.Settings()

def database_pgsql_url_config():
    return str(setting().DB_CONNECTION +"://"+setting().DB_USERNAME+":"+setting().DB_PASSWORD+
               "@"+setting().DB_HOST+":"+setting().DB_PORT+"/"+setting().DB_DATABASE)

database=databases.Database(database_pgsql_url_config())
engine=create_engine(database_pgsql_url_config())
metadata.create_all(engine)