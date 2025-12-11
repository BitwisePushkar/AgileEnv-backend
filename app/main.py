from fastapi import FastAPI,Request
from app.auth.router import router as auth_router
from app.auth.githubrouter import router as github_router
from app.auth.googlerouter import router as google_router
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter=Limiter(key_func=get_remote_address)

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="API documentation for Alige Backend",
    description="All APIs made for the Alige webapp- a modern and interactive Jira based webapp with multiple functionalities ",
    version="1.0",
    openapi_url="/openapi.json"
)
app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@limiter.limit("5/minute")
def root(request:Request):
    return {"message": "Welcome to Alige Backend"}

@app.api_route("/health",methods=["GET","HEAD"])
@limiter.limit("200/minute")
def health_check(request:Request):
    return {"status":"OK","service": "Alige Backend","version": "1.0"}

app.include_router(auth_router, tags=["Authentication"])
app.include_router(github_router,tags=["Github OAuth"])
app.include_router(google_router, tags=["Google OAuth"])