import json
import time
import random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
CELL_ID = "cell1"
TOPIC = f"battery/{CELL_ID}/telemetry"

client = mqtt.Client()
client.connect(BROKER, PORT)

voltage = 3.9
temperature = 25.0

print(f"Simulator started. Publishing to {TOPIC} every 1 second. Press Ctrl+C to stop.")

try:
    while True:
        current = -2.0 + random.uniform(-0.1, 0.1)
        voltage += random.uniform(-0.005, 0.005)
        temperature += random.uniform(-0.1, 0.1)

        reading = {
            "cell_id": CELL_ID,
            "ts": datetime.now(timezone.utc).isoformat(),
            "voltage": round(voltage, 3),
            "current": round(current, 3),
            "temperature": round(temperature, 2),
        }

        client.publish(TOPIC, json.dumps(reading))
        print(reading)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nSimulator stopped.")
    client.disconnect()