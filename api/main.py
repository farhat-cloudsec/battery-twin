import os
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "twin",
    "password": os.environ.get("POSTGRES_PASSWORD", "change_me"),
    "dbname": "batterytwin",
}

SECRET_KEY = os.environ.get("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Demo user. In a real system this would be a database table.
FAKE_USER = {
    "username": "admin",
    "hashed_password": pwd_context.hash(os.environ.get("ADMIN_PASSWORD", "change_me")),
}

app = FastAPI(title="Battery Digital Twin API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != FAKE_USER["username"] or not pwd_context.verify(
        form_data.password, FAKE_USER["hashed_password"]
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/cells/{cell_id}/latest")
def latest_reading(cell_id: str, current_user: str = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT row_to_json(r) FROM (
                        SELECT time, voltage, current, temperature
                        FROM readings WHERE cell_id = %s
                        ORDER BY time DESC LIMIT 1
                    ) r) AS reading,
                    (SELECT row_to_json(t) FROM (
                        SELECT soc, expected_voltage, residual, soh
                        FROM twin_state WHERE cell_id = %s
                        ORDER BY time DESC LIMIT 1
                    ) t) AS twin
                """,
                (cell_id, cell_id),
            )
            row = cur.fetchone()
            if row is None or row["reading"] is None:
                raise HTTPException(status_code=404, detail="No readings found for this cell")
            merged = {**row["reading"], **(row["twin"] or {})}
            return merged
    finally:
        conn.close()


@app.get("/cells/{cell_id}/history")
def history(cell_id: str, minutes: int = 30, current_user: str = Depends(get_current_user)):
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
                  AND r.time > NOW() - (%s * INTERVAL '1 minute')
                ORDER BY r.time ASC
                """,
                (cell_id, minutes),
            )
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/alerts")
def alerts(limit: int = 20, current_user: str = Depends(get_current_user)):
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