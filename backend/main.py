# main.py
from fastapi import FastAPI
from backend.routes import performance
from backend.routes import requirements_test


app = FastAPI(title="Backend PostgreSQL + Firebase")


app.include_router(requirements_test.router, prefix="/api")
app.include_router(performance.router, prefix="/api")
