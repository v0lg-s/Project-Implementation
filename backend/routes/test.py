# routes/test.py
from fastapi import APIRouter, Depends
from backend.db.postgres import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.firebase import db as firebase_db
from sqlalchemy import text # Import text for raw SQL queries

router = APIRouter()

@router.get("/users-from-sql")
async def get_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(text("SELECT user_id, username FROM app_user LIMIT 10;"))
    rows = result.fetchall()
    return [{"id": r[0], "username": r[1]} for r in rows]

@router.get("/videos-from-firebase")
async def get_videos():
    videos_ref = firebase_db.collection("Videos").limit(10)
    docs = videos_ref.stream()
    return [doc.to_dict() for doc in docs]
