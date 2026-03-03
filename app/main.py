from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.auth.router import router as auth_router
from app.auth.githubrouter import router as github_router
from app.auth.googlerouter import router as google_router
from app.workspace.routers import router as workspace_router
from app.chat.routers import router as chat_router
from app.project.routers import router as project_router
from app.kanban.routers import router as kanban_router
from app.scrum.routers import router as scrum_router
from app.utils.dbUtil import init_db, get_db
from app.utils.scheduler import start_scheduler, stop_scheduler
import asyncio
import logging

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

async def _blacklist_cleanup_task():
    while True:
        try:
            await asyncio.sleep(86400)
            db_gen = get_db()
            db = next(db_gen)
            try:
                from app.auth.crud import clear_blacklist
                deleted = clear_blacklist(db)
                logger.info(f"Blacklist cleanup: removed {deleted} expired entries")
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Blacklist cleanup task error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()                                 
    cleanup_task = asyncio.create_task(_blacklist_cleanup_task())
    logger.info("Agile backend started")
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    stop_scheduler()                                    
    logger.info("Agile backend stopped")

app = FastAPI(
    lifespan = lifespan,
    docs_url = "/api/docs",
    redoc_url = "/api/redocs",
    title = "Agile Backend API",
    description = "REST API for Agile — a modern Jira-inspired project management app.",
    version = "1.0",
    openapi_url = "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://alige-env-frontend-zs21.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@limiter.limit("100/minute")
def root(request: Request):
    return {"message": "Welcome to Agile Backend"}

@app.api_route("/health", tags=["System"])
@limiter.limit("200/minute")
def app_health_check(request: Request):
    return {"status": "OK", "service": "Agile Backend", "version": "1.0"}

app.include_router(auth_router, tags=["Authentication"])
app.include_router(github_router, tags=["GitHub OAuth"])
app.include_router(google_router, tags=["Google OAuth"])
app.include_router(workspace_router, tags=["Workspace"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(project_router, tags=["Project"])
app.include_router(kanban_router, tags=["Kanban"])
app.include_router(scrum_router, tags=["Scrum"])