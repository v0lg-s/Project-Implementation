import asyncpg
import asyncio
import time
import matplotlib.pyplot as plt

# Database connection configuration
DB_CONFIG = {
    'user': 'postgres',
    'password': 'root',
    'database': 'BD2-Project',
    'host': 'localhost',
    'port': '5432'
}

# SQL query template with dynamic LIMIT
QUERY_TEMPLATE = """
SELECT
    v.video_id,
    v.title,
    v.upload_datetime,
    v.visibility,
    au.username AS creator_username,
    COUNT(f.follower_id) AS follower_count
FROM video v
JOIN app_user au ON v.creator_id = au.user_id
LEFT JOIN follow f ON au.user_id = f.followed_id
WHERE v.creator_id IN (
    SELECT user_id FROM app_user WHERE role = 'creator' ORDER BY RANDOM()
)
GROUP BY v.video_id, v.title, v.upload_datetime, v.visibility, au.username
ORDER BY v.upload_datetime DESC
LIMIT {limit};
"""

# Limits for progressive load testing
LIMITS = [1000, 5000, 10000, 20000, 40000, 60000, 80000, 100000]

async def run_query(limit):
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        query = QUERY_TEMPLATE.format(limit=limit)
        start = time.time()
        await conn.fetch(query)
        end = time.time()
        elapsed_ms = (end - start) * 1000
        print(f"Retrieved {limit} rows in {elapsed_ms:.2f} ms")
        return limit, elapsed_ms
    except Exception as e:
        print(f"Error retrieving {limit} rows: {e}")
        return limit, None
    finally:
        await conn.close()

async def main():
    results = []
    for limit in LIMITS:
        limit_value, elapsed = await run_query(limit)
        if elapsed is not None:
            results.append((limit_value, elapsed))

    # Plotting
    limits, times = zip(*results)
    plt.figure(figsize=(10, 6))
    plt.plot(limits, times, marker='o')
    plt.title('PostgreSQL Performance Test: Rows Retrieved vs Response Time', fontsize=14)
    plt.xlabel('Rows Retrieved', fontsize=12)
    plt.ylabel('Response Time (ms)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('postgres_performance_test.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    asyncio.run(main())
