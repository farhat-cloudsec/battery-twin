import json
import os
import psycopg2
from pydantic import BaseModel, ValidationError
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "battery/+/telemetry"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "twin",
    "password": os.environ.get("POSTGRES_PASSWORD", "change_me"),
    "dbname": "batterytwin",
}


class Reading(BaseModel):
    cell_id: str
    ts: str
    voltage: float
    current: float
    temperature: float


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected to MQTT broker (rc={rc}). Subscribing to {TOPIC}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        reading = Reading(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Invalid message, skipping: {e}")
        return

    conn = userdata["conn"]
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO readings (time, cell_id, voltage, current, temperature)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (reading.ts, reading.cell_id, reading.voltage, reading.current, reading.temperature),
        )
    conn.commit()
    print(f"Saved: {reading.cell_id} at {reading.ts}")


def main():
    conn = get_connection()
    client = mqtt.Client(userdata={"conn": conn})
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)

    print("Ingestion service started. Press Ctrl+C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nIngestion service stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()