import os
from fastapi import FastAPI, HTTPException
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "twin",
    "password": os.environ.get("POSTGRES_PASSWORD", "change_me"),
    "dbname": "batterytwin",
}

app = FastAPI(title="Battery Digital Twin API")


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/cells/{cell_id}/latest")
def latest_reading(cell_id: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.time, r.voltage, r.current, r.temperature,
                       t.soc, t.expected_voltage, t.residual, t.soh
                FROM readings r
                LEFT JOIN twin_state t
                  ON t.cell_id = r.cell_id AND t.time = r.time
                WHERE r.cell_id = %s
                ORDER BY r.time DESC
                LIMIT 1
                """,
                (cell_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="No readings found for this cell")
            return row
    finally:
        conn.close()


@app.get("/cells/{cell_id}/history")
def history(cell_id: str, minutes: int = 30):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.time, r.voltage, r.current, r.temperature,
                       t.soc, t.expected_voltage, t.residual, t.soh
                FROM readings r
                LEFT JOIN twin_state t
                  ON t.cell_id = r.cell_id AND t.time = r.time
                WHERE r.cell_id = %s
                  AND r.time > NOW() - (%s || ' minutes')::INTERVAL
                ORDER BY r.time ASC
                """,
                (cell_id, minutes),
            )
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/alerts")
def alerts(limit: int = 20):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, time, cell_id, severity, message
                FROM alerts
                ORDER BY time DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()