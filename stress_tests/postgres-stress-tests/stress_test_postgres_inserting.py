import psycopg2
from faker import Faker
from datetime import datetime
import time

# === CONFIGURACIÓN POSTGRESQL ===
DB_PARAMS = {
    "dbname": "BD2-Project",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

faker = Faker()

def insert_users(n=1000):
    start = time.time()
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    try:
        for i in range(n):
            cur.execute("""
                INSERT INTO app_user (name, last_name, username, email, password_hash, registration_date, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                faker.first_name(),
                faker.last_name(),
                f"{faker.user_name()}_{faker.random_number(digits=5)}",
                faker.unique.email(),
                faker.sha256(),
                datetime.utcnow(),
                faker.random_element(elements=("user", "creator", "admin", "advertiser"))
            ))
            if (i + 1) % 200 == 0:
                conn.commit()
                print(f"✅ Inserted {i + 1} users...")

        conn.commit()
        end = time.time()
        print(f"✅ Inserted {n} users into PostgreSQL in {round(end - start, 2)} seconds.")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_users()
