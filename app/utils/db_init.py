import sys
import logging
from sqlalchemy import text
from app.utils.dbUtil import engine, Base
import app.auth.models                 
import app.workspace.model             
import app.project.model             
import app.kanban.models               
import app.scrum.model                
import app.chat.models             

logging.basicConfig(level = logging.INFO, format = "%(asctime)s [db-init] %(levelname)s: %(message)s",)
logger = logging.getLogger(__name__)

def init_db() -> None:
    logger.info("Connecting to database...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except Exception as e:
        logger.error(f"Cannot connect to database: {e}")
        sys.exit(1)
    logger.info("Running create_all — creating tables and ENUM types...")
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database initialisation complete — all tables and ENUMs ready")
    except Exception as e:
        logger.error(f"Database initialisation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
    sys.exit(0)