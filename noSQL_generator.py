import psycopg2
import firebase_admin
from firebase_admin import credentials, firestore
from faker import Faker
import random
from datetime import datetime

# === CONFIGURACIÓN ===
DB_PARAMS = {
    "dbname": "BD2-Project",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}
BLOCK_SIZE = 100  # SOLO 100 VIDEOS
FIREBASE_CRED_PATH = "./backend/firebase_credentials.json"

# === INICIALIZACIÓN ===
print("⚙️ Conectando a Firebase y PostgreSQL...")
cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred)
fs_db = firestore.client()

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

faker = Faker()

# === FUNCIONES FIRESTORE ===

def clean_firestore():
    print("🧹 Limpiando Firestore...")

    collections = ["Videos", "Reactions", "Views", "FeedCache"]
    for col in collections:
        docs = fs_db.collection(col).stream()
        for doc in docs:
            fs_db.collection(col).document(doc.id).delete()

    # Borrar subcolecciones Comments por video
    video_docs = fs_db.collection("Videos").stream()
    for doc in video_docs:
        comments = fs_db.collection("Videos").document(doc.id).collection("Comments").stream()
        for c in comments:
            fs_db.collection("Videos").document(doc.id).collection("Comments").document(c.id).delete()

    print("✅ Firestore limpio.")

def fetch_video_block(offset, limit):
    cur.execute("""
        SELECT video_id, creator_id, title, description, duration, upload_datetime, visibility
        FROM video
        ORDER BY video_id
        LIMIT %s OFFSET %s;
    """, (limit, offset))
    return cur.fetchall()

def get_all_users_and_videos():
    cur.execute("SELECT user_id FROM app_user WHERE role IN ('user', 'creator');")
    user_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT video_id FROM video;")
    video_ids = [r[0] for r in cur.fetchall()]
    return user_ids, video_ids

def generate_comments(user_ids, count):
    return [{
        "user_id": random.choice(user_ids),
        "text": faker.sentence(nb_words=12),
        "timestamp": faker.date_time_this_year()
    } for _ in range(count)]

def generate_views(user_ids, video_id, count):
    return [{
        "user_id": random.choice(user_ids),
        "video_id": str(video_id),
        "watch_time_sec": random.randint(5, 300),
        "timestamp": faker.date_time_this_year()
    } for _ in range(count)]

def generate_reactions(user_ids, video_id, count):
    types = ["like", "love", "laugh", "angry"]
    return [{
        "user_id": random.choice(user_ids),
        "video_id": str(video_id),
        "type": random.choice(types),
        "timestamp": faker.date_time_this_year()
    } for _ in range(count)]

def populate_feed_cache(user_ids, video_ids):
    print("🌀 Generando FeedCache por usuario...")
    for uid in user_ids:
        rec = random.sample(video_ids, k=min(20, len(video_ids)))
        fs_db.collection("FeedCache").document(str(uid)).set({
            "videos": [str(v) for v in rec],
            "updated_at": datetime.now()
        })

# === EJECUCIÓN PRINCIPAL ===

try:
    #clean_firestore()
    user_ids, all_video_ids = get_all_users_and_videos()
    offset = 0

    print(f"🚀 Poblando Firestore por bloques de {BLOCK_SIZE} videos...")
    videos = fetch_video_block(offset, BLOCK_SIZE)
    if not videos:
        print("⚠️ No se encontraron videos en la base de datos para poblar.")
    else:
        for idx, v in enumerate(videos, 1):
            video_id = str(v[0])
            video_doc = {
                "creator_id": v[1],
                "title": v[2],
                "description": v[3],
                "duration": v[4],
                "upload_datetime": v[5],
                "visibility": v[6],
            }

            # Video document
            fs_db.collection("Videos").document(video_id).set(video_doc)

            # Número aleatorio controlado entre 100 y 200 por tipo
            comment_count = random.randint(0, 150)
            view_count = random.randint(0, 150)
            reaction_count = random.randint(0, 150)

            # Subcolección de comentarios
            comments = generate_comments(user_ids, comment_count)
            for c in comments:
                fs_db.collection("Videos").document(video_id).collection("Comments").add(c)

            # Reactions
            reactions = generate_reactions(user_ids, video_id, reaction_count)
            for r in reactions:
                fs_db.collection("Reactions").add(r)

            # Views
            views = generate_views(user_ids, video_id, view_count)
            for vw in views:
                fs_db.collection("Views").add(vw)

            print(f"✅ {idx}/{BLOCK_SIZE} Video {video_id} poblado con {comment_count} comentarios, {reaction_count} reacciones y {view_count} vistas.")

    # FeedCache por usuario
    #populate_feed_cache(user_ids, all_video_ids)

    print("✅ Firestore completamente poblado con 100 videos y carga controlada de interacciones.")

except Exception as e:
    print("❌ Error durante la ejecución:", e)
    print("🛑 Operación abortada. Firestore puede quedar parcialmente poblado.")
finally:
    cur.close()
    conn.close()
    print("🔒 Conexión cerrada.")
