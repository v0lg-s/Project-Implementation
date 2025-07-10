# db/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore
from backend.config import FIREBASE_CREDENTIALS

cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)
db = firestore.client()
