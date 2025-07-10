import firebase_admin
from firebase_admin import credentials, firestore
from faker import Faker
from datetime import datetime
import time

# === CONFIGURACIÓN FIRESTORE ===
cred = credentials.Certificate("./backend/firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

faker = Faker()

def insert_videos(n=1000):
    start = time.time()
    batch = db.batch()

    for i in range(n):
        doc_ref = db.collection("Videos").document()
        video_data = {
            "creator_id": faker.random_int(min=1, max=1000),
            "title": faker.sentence(nb_words=6),
            "description": faker.text(max_nb_chars=200),
            "duration": faker.random_int(min=10, max=600),
            "upload_datetime": datetime.utcnow(),
            "visibility": faker.random_element(elements=("public", "private", "followers_only")),
        }
        batch.set(doc_ref, video_data)

        # Commit cada 500 para evitar límites de Firestore
        if (i + 1) % 500 == 0:
            batch.commit()
            batch = db.batch()
            print(f"✅ Inserted {i + 1} videos...")

    # Commit final
    batch.commit()
    end = time.time()
    print(f"✅ Inserted {n} videos into Firestore in {round(end - start, 2)} seconds.")

if __name__ == "__main__":
    insert_videos()
