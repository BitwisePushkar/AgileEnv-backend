from fastapi import FastAPI
from app.auth import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="API for Agile Backend",
    description="All API made for Agile",
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
    return {"message": "Welcome to Agile Backend"}

app.include_router(router.router, tags=["auth"])