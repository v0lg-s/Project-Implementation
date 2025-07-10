# backend/routes/performance.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.db.postgres import get_session
from backend.db.firebase import db as firebase_db
import time
import random

router = APIRouter()

# 1️ PostgreSQL - Ingestión masiva de 1000 usuarios
@router.post("/test-bigdata/postgres-bulk-insert")
async def postgres_bulk_insert(
    batch_size: int = Query(1000, ge=10, le=5000),
    session: AsyncSession = Depends(get_session)
):
    import time
    start = time.time()
    try:
        # 1️⃣ Obtener el último índice generado en username de pruebas anteriores
        result = await session.execute(text("""
            SELECT MAX(CAST(SUBSTRING(username FROM 'bigdata_user_(\\d+)') AS INTEGER)) AS last_index
            FROM app_user
            WHERE username LIKE 'bigdata_user_%';
        """))
        last_index = result.scalar()
        start_index = last_index + 1 if last_index is not None else 0

        # 2️⃣ Insertar batch_size usuarios a partir de start_index
        for i in range(start_index, start_index + batch_size):
            await session.execute(text("""
                INSERT INTO app_user (name, last_name, username, email, password_hash, role)
                VALUES (:name, :last_name, :username, :email, :password_hash, :role)
            """), {
                "name": f"Name{i}",
                "last_name": f"Last{i}",
                "username": f"bigdata_user_{i}",
                "email": f"bigdata_user_{i}@example.com",
                "password_hash": "hash",
                "role": "user"
            })

        await session.commit()
        end = time.time()
        return {
            "message": f"Inserted {batch_size} users starting from index {start_index}",
            "time_ms": round((end - start) * 1000, 2)
        }

    except Exception as e:
        await session.rollback()
        return {"error": str(e)}




# 2️ PostgreSQL - retrieving 1000 users
@router.get("/test-bigdata/postgres-retrieve-users")
async def postgres_retrieve_users(batch_size: int = Query(1000, ge=100, le=10000), session: AsyncSession = Depends(get_session)):
    import time
    start = time.time()
    result = await session.execute(text(f"""
        SELECT user_id, username, email, role
        FROM app_user
        LIMIT {batch_size};
    """))
    rows = result.mappings().all()
    end = time.time()
    return {
        "execution_time_ms": round((end - start) * 1000, 2),
        "users_retrieved": len(rows),
        "sample": rows[:10]
    }



# 3️ Firebase - Ingestión masiva de x vistas
from faker import Faker
faker = Faker()

@router.post("/test-bigdata/firebase-insert-views")
async def firebase_insert_views(batch_size: int = Query(1000, ge=1, le=5000)):
    from datetime import datetime
    import time
    video_id = "150002"  # Video fijo para la prueba

    batch = firebase_db.batch()

    for i in range(batch_size):
        doc_ref = firebase_db.collection("Views").document()
        view_data = {
            "video_id": video_id,
            "user_id": str(faker.random_int(min=1, max=10000)),
            "watch_time_sec": faker.random_int(min=5, max=600),
            "timestamp": faker.date_time_this_year()
        }
        batch.set(doc_ref, view_data)

        # For large inserts, commit every 500
        if (i + 1) % 500 == 0:
            commit_start = time.time()
            batch.commit()
            commit_end = time.time()
            print(f"✅ Inserted {i+1} views in {round((commit_end - commit_start)*1000, 2)} ms")
            batch = firebase_db.batch()

    # Final commit measurement
    commit_start = time.time()
    batch.commit()
    commit_end = time.time()

    return {
        "message": f"Inserted {batch_size} views into Firestore for video_id '{video_id}'",
        "video_id": video_id,
        "commit_time_ms": round((commit_end - commit_start) * 1000, 2)
    }



# 4️ Firebase - retrieval of x views
@router.get("/test-bigdata/firestore-retrieve-views")
async def firestore_retrieve_views(
    video_id: str = Query(...),
    batch_size: int = Query(1000, ge=100, le=5000)
):
    import time
    start = time.time()
    docs = firebase_db.collection("Views").where("video_id", "==", video_id).limit(batch_size).stream()
    retrieved_docs = []
    count = 0
    for doc in docs:
        retrieved_docs.append(doc.to_dict())
        count += 1
    end = time.time()
    return {
        "video_id": video_id,
        "execution_time_ms": round((end - start) * 1000, 2),
        "documents_retrieved": count,
        "sample": retrieved_docs[:3]
    }


# 6️ PostgreSQL - Videos recientes (stress test)
@router.get("/test-bigdata/performance/trending-videos-sql")
async def trending_videos_sql(session: AsyncSession = Depends(get_session)):
    start = time.time()
    result = await session.execute(text("""
        SELECT
            v.video_id,
            v.title,
            v.upload_datetime,
            v.visibility,
            au.username AS creator_username
        FROM video v
        JOIN app_user au ON v.creator_id = au.user_id
        WHERE v.upload_datetime >= NOW() - INTERVAL '7 days'
        ORDER BY v.upload_datetime DESC
    """))
    rows = result.fetchall()
    end = time.time()
    return {
        "execution_time_ms": round((end - start) * 1000, 2),
        "total_results": len(rows),
        "sample": [dict(zip([col for col in result.keys()], row)) for row in rows[:10]]
    }





