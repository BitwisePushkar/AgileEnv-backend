from fastapi import FastAPI
from app.routes import auth

app = FastAPI(title="API for Agile Backend")

app.include_router(auth.router, prefix="/auth", tags=["authentication"])

@app.get("/")
def root():
    return {"message": "Welcome to Agile Backend"}