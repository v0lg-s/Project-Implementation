import psycopg2
from faker import Faker
import random
from datetime import timedelta

fake = Faker()


conn = psycopg2.connect(
    dbname="BD2-Project",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

def clean_database():
    print("🧹 Limpiando todas las tablas...")

    try:
        cur.execute("SET session_replication_role = replica;")  # Desactiva restricciones FK temporalmente

        # Orden de borrado: desde las tablas más dependientes a las más generales
        tables = [
            'gifttransaction',
            'contentreport',
            'transaction',
            'virtualgift',
            'subscription',
            'subscriptionplan',
            'campaign',
            'advertiser',
            'video',
            'follow',
            'app_user'
        ]

        for table in tables:
            cur.execute(f"DELETE FROM {table};")
            print(f" - {table} vaciada")

        cur.execute("SET session_replication_role = DEFAULT;")  # Reactiva restricciones

        conn.commit()
        print("✅ Base de datos limpia.")
    except Exception as e:
        print("❌ Error limpiando base de datos:", e)
        conn.rollback()

def generate_users(total=10000):
    print(f"🔹 Generando {total} usuarios...")
    roles = ['user'] * 85 + ['creator'] * 10 + ['admin'] * 5
    try:
        for i in range(total):
            role = random.choice(roles)
            cur.execute("""
                INSERT INTO app_user (name, last_name, username, email, password_hash, registration_date, profile_pic_url, role, birth_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fake.first_name(),
                fake.last_name(),
                f"user{i}_{fake.user_name()}",
                fake.unique.email(),
                fake.sha256(),
                fake.date_time_this_decade(),
                fake.image_url(),
                role,
                fake.date_of_birth(minimum_age=16, maximum_age=40)
            ))
            if i % 500 == 0:
                conn.commit()
                print(f"> {i} usuarios insertados...")
        conn.commit()
    except Exception as e:
        print("❌ Error generando usuarios:", e)
        conn.rollback()

def generate_advertisers(n=500):
    print(f"🔹 Generando {n} advertisers...")
    try:
        for i in range(n):
            cur.execute("""
                INSERT INTO advertiser (company_name, billing_info)
                VALUES (%s, %s)
            """, (
                fake.company(),
                fake.address()
            ))
        conn.commit()
    except Exception as e:
        print("❌ Error en advertisers:", e)
        conn.rollback()

def generate_campaigns(n=2000):
    print(f"🔹 Generando {n} campañas...")
    try:
        cur.execute("SELECT advertiser_id FROM advertiser")
        advertisers = [r[0] for r in cur.fetchall()]
        for i in range(n):
            adv = random.choice(advertisers)
            start = fake.date_this_year()
            end = start + timedelta(days=random.randint(7, 30))
            cur.execute("""
                INSERT INTO campaign (advertiser_id, budget, start_date, end_date, targeting_criteria)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                adv,
                round(random.uniform(100.0, 5000.0), 2),
                start,
                end,
                fake.sentence(nb_words=6)
            ))
            if i % 500 == 0:
                conn.commit()
                print(f"> {i} campañas insertadas...")
        conn.commit()
    except Exception as e:
        print("❌ Error en campañas:", e)
        conn.rollback()

def generate_subscription_plans():
    print("🔹 Generando planes de suscripción...")
    try:
        plans = [
            ("Starter", 5, 30, "Acceso básico."),
            ("Pro", 15, 90, "Contenido extendido."),
            ("Elite", 30, 180, "Experiencia completa.")
        ]
        for name, price, duration, desc in plans:
            cur.execute("""
                INSERT INTO subscriptionplan (name, price, duration_days, description)
                VALUES (%s, %s, %s, %s)
            """, (name, price, duration, desc))
        conn.commit()
    except Exception as e:
        print("❌ Error en subscription plans:", e)
        conn.rollback()

def generate_videos(n=50000):
    print(f"🔹 Generando {n} videos...")
    try:
        cur.execute('SELECT user_id FROM app_user WHERE role = %s', ('creator',))
        creators = [r[0] for r in cur.fetchall()]
        vis = ['public', 'private', 'followers_only']
        for i in range(n):
            cur.execute("""
                INSERT INTO video (creator_id, title, description, duration, upload_datetime, visibility)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                random.choice(creators),
                fake.sentence(nb_words=6),
                fake.text(max_nb_chars=200),
                random.randint(10, 300),
                fake.date_time_this_year(),
                random.choice(vis)
            ))
            if i % 1000 == 0:
                conn.commit()
                print(f"> {i} videos insertados...")
        conn.commit()
    except Exception as e:
        print("❌ Error en videos:", e)
        conn.rollback()

def generate_subscriptions(n=20000):
    print(f"🔹 Generando {n} suscripciones...")
    try:
        cur.execute("SELECT user_id FROM app_user WHERE role = %s", ('user',))
        subs = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT user_id FROM app_user WHERE role = %s", ('creator',))
        creators = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT plan_id FROM subscriptionplan")
        plans = [r[0] for r in cur.fetchall()]
        statuses = ['active', 'cancelled', 'expired']
        for i in range(n):
            cur.execute("""
                INSERT INTO subscription (subscriber_id, creator_id, plan_id, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                random.choice(subs),
                random.choice(creators),
                random.choice(plans),
                fake.date_this_year(),
                fake.date_this_year(),
                random.choice(statuses)
            ))
            if i % 1000 == 0:
                conn.commit()
                print(f"> {i} suscripciones insertadas...")
        conn.commit()
    except Exception as e:
        print("❌ Error en suscripciones:", e)
        conn.rollback()

def generate_virtual_gifts():
    print("🔹 Generando regalos virtuales...")
    gifts = [
        ("Rose", 1.0),
        ("Coffee", 2.0),
        ("Diamond", 5.0),
        ("Super Like", 3.5),
        ("Rocket", 10.0)
    ]
    try:
        for name, price in gifts:
            cur.execute("""
                INSERT INTO virtualgift (name, price)
                VALUES (%s, %s)
            """, (name, price))
        conn.commit()
    except Exception as e:
        print("❌ Error en virtualgift:", e)
        conn.rollback()

def generate_transactions(n=50000):
    print(f"🔹 Generando {n} transacciones...")
    try:
        cur.execute("SELECT user_id FROM app_user")
        users = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT advertiser_id FROM advertiser")
        advertisers = [r[0] for r in cur.fetchall()]
        currencies = ['USD', 'COP', 'EUR']
        types = ['subscription', 'gift', 'ad_payment']

        for i in range(n):
            t_type = random.choice(types)
            user = random.choice(users)
            adv = random.choice(advertisers) if t_type == 'ad_payment' else None
            cur.execute("""
                INSERT INTO transaction (user_id, advertiser_id, amount, currency, type, transaction_datetime, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user,
                adv,
                round(random.uniform(0.99, 100.00), 2),
                random.choice(currencies),
                t_type,
                fake.date_time_this_year(),
                random.choice([True, True, False])
            ))
            if i % 1000 == 0:
                conn.commit()
                print(f"> {i} transacciones insertadas...")
        conn.commit()
    except Exception as e:
        print("❌ Error en transacciones:", e)
        conn.rollback()

def generate_gift_transactions(n=20000):
    print(f"🔹 Generando {n} gifttransactions...")
    try:
        cur.execute("SELECT transaction_id FROM transaction WHERE type = 'gift'")
        gift_txs = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT user_id FROM app_user")
        users = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT gift_id FROM virtualgift")
        gifts = [r[0] for r in cur.fetchall()]

        for i in range(n):
            tx_id = random.choice(gift_txs)
            sender = random.choice(users)
            receiver = random.choice([u for u in users if u != sender])
            gift = random.choice(gifts)
            cur.execute("""
                INSERT INTO gifttransaction (transaction_id, sender_id, receiver_id, gift_id)
                VALUES (%s, %s, %s, %s)
            """, (
                tx_id,
                sender,
                receiver,
                gift
            ))
            if i % 1000 == 0:
                conn.commit()
                print(f"> {i} regalos insertados...")
        conn.commit()
    except Exception as e:
        print("❌ Error en gifttransaction:", e)
        conn.rollback()

def generate_content_reports(n=5000):
    print(f"🔹 Generando {n} reportes de contenido...")
    try:
        cur.execute("SELECT video_id FROM video")
        videos = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT user_id FROM app_user WHERE role IN ('user', 'creator')")
        reporters = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT user_id FROM app_user WHERE role = 'admin'")
        moderators = [r[0] for r in cur.fetchall()]
        statuses = ['pending', 'resolved', 'rejected']
        reasons = ['Inappropriate content', 'Spam', 'Copyright issue', 'Hate speech', 'Violence']

        for i in range(n):
            cur.execute("""
                INSERT INTO contentreport (video_id, reporter_id, reviewed_by, reason, status, report_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                random.choice(videos),
                random.choice(reporters),
                random.choice(moderators) if random.random() > 0.5 else None,
                random.choice(reasons),
                random.choice(statuses),
                fake.date_time_this_year()
            ))
            if i % 500 == 0:
                conn.commit()
                print(f"> {i} reportes insertados...")
        conn.commit()
    except Exception as e:
        print("❌ Error en contentreport:", e)
        conn.rollback()

# =====================
# EJECUCIÓN PRINCIPAL
# =====================
try:
    generate_users(10000)
    generate_advertisers(500)
    generate_campaigns(2000)
    generate_subscription_plans()
    generate_videos(100000)
    generate_subscriptions(20000)
    generate_virtual_gifts()
    generate_transactions(50000)
    generate_gift_transactions(20000)
    generate_content_reports(5000)
    print("✅ Base de datos completamente poblada.")
except Exception as global_error:
    print("❌ Error global:", global_error)
    conn.rollback()
finally:
    cur.close()
    conn.close()
    print("🔒 Conexión cerrada.")
