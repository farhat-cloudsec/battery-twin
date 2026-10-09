import json
import time
import random
import threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
CELL_ID = "cell1"
TOPIC = f"battery/{CELL_ID}/telemetry"
CAPACITY_AH = 2.5
R0 = 0.05  # must match twin.py's R0 for the expected-voltage comparison to make sense

client = mqtt.Client()
client.connect(BROKER, PORT)

voltage = 3.9
temperature = 25.0
soc_estimate = 80.0  # simulator's own rough SoC tracker, used only to steer voltage
fault_until = 0  # timestamp until which a fault is active


def listen_for_fault():
    global fault_until
    while True:
        input()  # waits for you to press Enter
        fault_until = time.time() + 10
        print(">>> FAULT INJECTED for 10 seconds <<<")


threading.Thread(target=listen_for_fault, daemon=True).start()

print(f"Simulator started. Publishing to {TOPIC} every 1 second.")
print("Press Enter at any time to inject a 10-second fault. Press Ctrl+C to stop.")

try:
    while True:
        current = -2.0 + random.uniform(-0.1, 0.1)

        soc_estimate += (current * (1 / 3600)) / CAPACITY_AH * 100
        soc_estimate = max(0.0, min(100.0, soc_estimate))

        target_voltage = 3.0 + (soc_estimate / 100) * 1.2 - (current * R0)  # rough SoC-linked target
        voltage += (target_voltage - voltage) * 0.05 + random.uniform(-0.005, 0.005)

        temperature += random.uniform(-0.1, 0.1)

        if time.time() < fault_until:
            temperature += 15.0  # simulate overheating
            voltage -= 0.3       # simulate a voltage drop

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