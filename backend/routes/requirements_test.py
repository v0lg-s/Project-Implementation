# backend/routes/requirements_test.py

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.db.postgres import get_session
from backend.db.firebase import db as firebase_db
from pydantic import BaseModel
import time
import uuid
from datetime import datetime
from faker import Faker

router = APIRouter()
faker = Faker()
# 1️⃣ Functional Requirement #1: User Registration
class UserRegister(BaseModel):
    name: str
    last_name: str
    username: str
    email: str
    password: str

@router.post("/requirements/register")
async def register_user(user: UserRegister, session: AsyncSession = Depends(get_session)):
    start = time.time()
    try:
        await session.execute(text("""
            INSERT INTO app_user (name, last_name, username, email, password_hash, role)
            VALUES (:name, :last_name, :username, :email, :password_hash, 'user')
        """), {
            "name": user.name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "password_hash": user.password
        })
        await session.commit()
        end = time.time()
        return {"message": "User registered successfully", "time_ms": round((end - start) * 1000, 2)}
    except Exception as e:
        await session.rollback()
        return {"error": str(e)}

# 2️⃣ Functional Requirement #2: Video Upload
@router.post("/requirements/upload-video")
async def upload_video(
    creator_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    visibility: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    start = time.time()
    try:
        # Insertar en PostgreSQL
        result = await session.execute(text("""
            INSERT INTO video (creator_id, title, description, duration, visibility)
            VALUES (:creator_id, :title, :description, :duration, :visibility)
            RETURNING video_id, creator_id, title, description, duration, upload_datetime, visibility
        """), {
            "creator_id": creator_id,
            "title": title,
            "description": description,
            "duration": duration,
            "visibility": visibility
        })
        await session.commit()

        video_row = result.fetchone()
        if video_row is None:
            raise Exception("Error retrieving inserted video.")

        # Preparar documento para Firestore
        video_id, creator_id_db, title_db, description_db, duration_db, upload_datetime_db, visibility_db = video_row
        video_doc = {
            "creator_id": creator_id_db,
            "title": title_db,
            "description": description_db,
            "duration": duration_db,
            "upload_datetime": upload_datetime_db,
            "visibility": visibility_db,
        }

        # Insertar en Firestore
        firebase_db.collection("Videos").document(str(video_id)).set(video_doc)

        end = time.time()
        return {
            "message": "Video uploaded successfully to PostgreSQL and Firestore.",
            "video_id": video_id,
            "time_ms": round((end - start) * 1000, 2)
        }

    except Exception as e:
        await session.rollback()
        return {"error": str(e)}

# 3️⃣ Functional Requirement #3: Like, Comment, Follow
@router.post("/requirements/like-video")
async def like_video(video_id: str = Form(...),
    user_id: int = Form(...)
    ):
    doc_id = str(uuid.uuid4())
    firebase_db.collection("Reactions").document(doc_id).set({
        "video_id": video_id,
        "user_id": user_id,
        "type": "like",
        "timestamp": faker.date_time_this_year()
    })
    return {"message": f"User {user_id} liked video {video_id}."}

@router.post("/requirements/comment-video")
async def comment_video(video_id: str = Form(...),
    user_id: str = Form(...),
    comment: str = Form(...)
    ):
    firebase_db.collection("Videos").document(video_id).collection("Comments").add({
        "user_id": user_id,
        "text": comment,
        "timestamp": faker.date_time_this_year()
    })
    return {"message": f"Comment added to video {video_id}."}

@router.post("/requirements/follow-creator")
async def follow_creator(
    follower_id: int = Form(...),
    followed_id: int = Form(...),
    session: AsyncSession = Depends(get_session)
):
    await session.execute(text("""
        INSERT INTO follow (follower_id, followed_id)
        VALUES (:follower_id, :followed_id)
    """), {
        "follower_id": follower_id,
        "followed_id": followed_id
    })
    await session.commit()
    return {"message": f"User {follower_id} is now following user {followed_id}."}

# 4️⃣ Functional Requirement #4: Search videos with filters
@router.get("/requirements/search-videos")
async def search_videos(keyword: str, session: AsyncSession = Depends(get_session)):
    start = time.time()
    result = await session.execute(text("""
        SELECT video_id, title, description, upload_datetime
        FROM video
        WHERE title ILIKE :keyword OR description ILIKE :keyword
        ORDER BY upload_datetime DESC
        LIMIT 20
    """), {"keyword": f"%{keyword}%"})
    videos = result.mappings().all()  # ✅ devuelve una lista de diccionarios directamente
    end = time.time()
    return {"results": videos, "time_ms": round((end - start) * 1000, 2)}

# 5️⃣ Functional Requirement #5: Report inappropriate content
@router.post("/requirements/report-video")
async def report_video(
    video_id: int = Form(...),
    reporter_id: int = Form(...),
    reason: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    await session.execute(text("""
        INSERT INTO contentreport (video_id, reporter_id, reason)
        VALUES (:video_id, :reporter_id, :reason)
    """), {
        "video_id": video_id,
        "reporter_id": reporter_id,
        "reason": reason
    })
    await session.commit()
    return {"message": f"Video {video_id} reported by user {reporter_id} for reason: {reason}"}


# 6️⃣ Functional Requirement #6: Advertiser - Create campaign
@router.post("/requirements/create-campaign")
async def create_campaign(
    advertiser_id: int = Form(...),
    budget: float = Form(...),
    targeting: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    await session.execute(text("""
        INSERT INTO campaign (advertiser_id, budget, start_date, end_date, targeting_criteria)
        VALUES (:advertiser_id, :budget, NOW(), NOW() + INTERVAL '30 days', :targeting_criteria)
    """), {
        "advertiser_id": advertiser_id,
        "budget": budget,
        "targeting_criteria": targeting
    })
    await session.commit()
    return {"message": f"Campaign created for advertiser {advertiser_id}."}


# 7️⃣ Functional Requirement #6: Advertiser - View campaign analytics
@router.get("/requirements/campaign-analytics")
async def campaign_analytics(advertiser_id: int, session: AsyncSession = Depends(get_session)):
    start = time.time()
    result = await session.execute(text("""
        SELECT c.campaign_id, c.budget, c.start_date, c.end_date,
               COUNT(t.transaction_id) AS transactions,
               SUM(t.amount) AS total_spent
        FROM campaign c
        LEFT JOIN transaction t ON t.advertiser_id = c.advertiser_id
        WHERE c.advertiser_id = :advertiser_id
        GROUP BY c.campaign_id
    """), {"advertiser_id": advertiser_id})
    
    campaigns = result.mappings().all()  # ✅ forma correcta
    end = time.time()
    return {"results": campaigns, "time_ms": round((end - start) * 1000, 2)}

# 8️⃣ Functional Requirement #7: Creator - Access video statistics
from datetime import datetime, timedelta

@router.get("/requirements/creator-video-analytics")
async def creator_video_analytics(creator_id: int, session: AsyncSession = Depends(get_session)):
    start = time.time()

    # 1️⃣ Total de videos y duración promedio
    result = await session.execute(text("""
        SELECT COUNT(*) AS total_videos, COALESCE(AVG(duration), 0) AS avg_duration
        FROM video
        WHERE creator_id = :creator_id
    """), {"creator_id": creator_id})
    row = result.mappings().first()
    total_videos = row["total_videos"]
    avg_duration = round(row["avg_duration"], 2)

    # 2️⃣ Vistas y reacciones en la última semana desde Firestore
    one_week_ago = datetime.utcnow() - timedelta(days=7)

    # Vistas
    views_query = firebase_db.collection("Views").where("timestamp", ">=", one_week_ago).stream()
    total_views = sum(1 for _ in views_query)

    # Reacciones
    reactions_query = firebase_db.collection("Reactions").where("timestamp", ">=", one_week_ago).stream()
    total_reactions = sum(1 for _ in reactions_query)

    end = time.time()

    return {
        "creator_id": creator_id,
        "total_videos": total_videos,
        "average_video_duration_sec": avg_duration,
        "total_views_last_7_days": total_views,
        "total_reactions_last_7_days": total_reactions,
        "time_ms": round((end - start) * 1000, 2)
    }

