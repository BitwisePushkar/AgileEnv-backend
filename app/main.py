from fastapi import FastAPI
from app.auth.router import router as auth_router
from app.auth.githubrouter import router as github_router
from app.auth.googlerouter import router as google_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="API documentation for Alige Backend",
    description="All APIs made for the Alige webapp- a modern and interactive Jira based webapp with multiple functionalities ",
    version="1.0",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to Alige Backend"}

@app.get("/health")
def health_check():
    return {"status":"OK","service": "Alige Backend","version": "1.0"}

app.include_router(auth_router, tags=["Authentication"])
app.include_router(github_router,tags=["Github OAuth"])
app.include_router(google_router, tags=["Google OAuth"])