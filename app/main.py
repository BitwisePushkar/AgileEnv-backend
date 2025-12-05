from fastapi import FastAPI
from app.utils.dbUtil import database

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redocs",
    title="API for Agile Backend",
    description="All api made for Agile",
    version="1.0",
    openapi_url="/openapi.json"
    )

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
def root():
    return {"message": "Welcome to Agile Backend"}

# app.include_router(auth.router, prefix="/auth", tags=["authentication"])
