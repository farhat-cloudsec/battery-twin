import os
import time
import joblib
import pandas as pd
import psycopg2
from datetime import datetime, timezone

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "twin",
    "password": os.environ.get("POSTGRES_PASSWORD", "change_me"),
    "dbname": "batterytwin",
}

CAPACITY_AH = 2.5  # battery's nominal capacity in amp-hours (used for SoC)
CELL_ID = "cell1"
R0 = 0.05  # internal resistance in ohms
RESIDUAL_THRESHOLD = 0.1  # volts; above this, we flag an anomaly

# Start at 80% charge. In a real system this would come from the last known value.
soc = 80.0
cycle_count = 0  # simple proxy for "how aged" the simulated cell is

# Load the SoH model trained on real NASA battery data
soh_bundle = joblib.load("twin/soh_model.joblib")
soh_model = soh_bundle["model"]
soh_nominal_capacity = soh_bundle["nominal_capacity"]


def expected_voltage(soc_value, current):
    ocv = 3.0 + (soc_value / 100) * 1.2  # simple open-circuit voltage model (3.0V to 4.2V)
    return ocv - (current * R0)


def predict_soh(cycle):
    predicted_capacity = soh_model.predict(pd.DataFrame({"cycle": [cycle]}))[0]
    soh = (predicted_capacity / soh_nominal_capacity) * 100
    return float(max(0.0, min(100.0, soh)))


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_new_readings(conn, last_time):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT time, current, voltage
            FROM readings
            WHERE cell_id = %s AND time > %s
            ORDER BY time ASC
            """,
            (CELL_ID, last_time),
        )
        return cur.fetchall()


def save_twin_state(conn, t, cell_id, soc_value, v_exp, residual, soh_value):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO twin_state (time, cell_id, soc, expected_voltage, residual, soh)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (t, cell_id, soc_value, v_exp, residual, soh_value),
        )
    conn.commit()


def save_alert(conn, t, cell_id, message):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO alerts (time, cell_id, severity, message)
            VALUES (%s, %s, %s, %s)
            """,
            (t, cell_id, "HIGH", message),
        )
    conn.commit()


def main():
    global soc, cycle_count
    conn = get_connection()
    last_time = datetime.now(timezone.utc).isoformat()  # only process readings from now onward

    print("Twin service started. Press Ctrl+C to stop.")
    try:
        while True:
            rows = get_new_readings(conn, last_time)
            for t, current, voltage_measured in rows:
                dt_hours = 1 / 3600  # readings arrive every 1 second
                soc += (current * dt_hours) / CAPACITY_AH * 100
                soc = max(0.0, min(100.0, soc))  # keep between 0 and 100

                cycle_count += 1 / 3600  # roughly simulate aging over time, for demo purposes

                v_exp = expected_voltage(soc, current)
                residual = voltage_measured - v_exp
                soh_value = predict_soh(cycle_count)

                save_twin_state(conn, t, CELL_ID, soc, v_exp, residual, soh_value)
                print(
                    f"{t}  SoC={soc:.2f}%  V_expected={v_exp:.3f}V  "
                    f"Residual={residual:.3f}V  SoH={soh_value:.2f}%"
                )

                if abs(residual) > RESIDUAL_THRESHOLD:
                    msg = f"Voltage residual {residual:.3f}V exceeds threshold ({RESIDUAL_THRESHOLD}V)"
                    save_alert(conn, t, CELL_ID, msg)
                    print(f"  !! ALERT: {msg}")

                last_time = t

            time.sleep(2)
    except KeyboardInterrupt:
        print("\nTwin service stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()