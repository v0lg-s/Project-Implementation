import firebase_admin
from firebase_admin import credentials, firestore
import time

# === CONFIGURACIÓN FIRESTORE ===
cred = credentials.Certificate("./backend/firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def retrieve_videos(n=1000):
    start = time.time()

    docs = db.collection("Videos").limit(n).stream()
    videos = []

    count = 0
    for doc in docs:
        videos.append(doc.to_dict())
        count += 1
        if count % 200 == 0:
            print(f"✅ Retrieved {count} videos...")

    end = time.time()

    print(f"✅ Retrieved {count} videos from Firestore in {round(end - start, 2)} seconds.")
    print("\nSample documents:")
    for vid in videos[:3]:
        print(vid)

if __name__ == "__main__":
    retrieve_videos()
