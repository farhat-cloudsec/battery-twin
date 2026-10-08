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
R0 = 0.05  # internal resistance in ohms
RESIDUAL_THRESHOLD = 0.1  # volts; above this, we flag an anomaly

# Start at 80% charge. In a real system this would come from the last known value.
soc = 80.0


def expected_voltage(soc_value, current):
    ocv = 3.0 + (soc_value / 100) * 1.2  # simple open-circuit voltage model (3.0V to 4.2V)
    return ocv - (current * R0)


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


def save_twin_state(conn, t, cell_id, soc_value, v_exp, residual):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO twin_state (time, cell_id, soc, expected_voltage, residual)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (t, cell_id, soc_value, v_exp, residual),
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
    global soc
    conn = get_connection()
    last_time = "2000-01-01T00:00:00Z"  # start from the beginning

    print("Twin service started. Press Ctrl+C to stop.")
    try:
        while True:
            rows = get_new_readings(conn, last_time)
            for t, current, voltage_measured in rows:
                dt_hours = 1 / 3600  # readings arrive every 1 second
                soc += (current * dt_hours) / CAPACITY_AH * 100
                soc = max(0.0, min(100.0, soc))  # keep between 0 and 100

                v_exp = expected_voltage(soc, current)
                residual = voltage_measured - v_exp

                save_twin_state(conn, t, CELL_ID, soc, v_exp, residual)
                print(f"{t}  SoC={soc:.2f}%  V_expected={v_exp:.3f}V  Residual={residual:.3f}V")

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