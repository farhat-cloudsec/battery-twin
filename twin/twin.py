import os
import time
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "twin",
    "password": os.environ.get("POSTGRES_PASSWORD", "change_me"),
    "dbname": "batterytwin",
}

CAPACITY_AH = 2.5  # battery's nominal capacity in amp-hours
CELL_ID = "cell1"

# Start at 80% charge. In a real system this would come from the last known value.
soc = 80.0


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_new_readings(conn, last_time):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT time, current
            FROM readings
            WHERE cell_id = %s AND time > %s
            ORDER BY time ASC
            """,
            (CELL_ID, last_time),
        )
        return cur.fetchall()


def save_twin_state(conn, t, cell_id, soc_value):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO twin_state (time, cell_id, soc)
            VALUES (%s, %s, %s)
            """,
            (t, cell_id, soc_value),
        )
    conn.commit()


def main():
    global soc
    conn = get_connection()
    last_time = "2000-01-01T00:00:00Z"  # start from the beginning

    print("Twin service started. Press Ctrl+C to stop.")
    try:
        while True:
            rows = get_new_readings(conn, last_time)
            for t, current in rows:
                dt_hours = 1 / 3600  # readings arrive every 1 second
                soc += (current * dt_hours) / CAPACITY_AH * 100
                soc = max(0.0, min(100.0, soc))  # keep between 0 and 100

                save_twin_state(conn, t, CELL_ID, soc)
                print(f"{t}  SoC={soc:.2f}%")
                last_time = t

            time.sleep(2)
    except KeyboardInterrupt:
        print("\nTwin service stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()