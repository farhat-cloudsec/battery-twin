# Battery Digital Twin

Simulated battery digital twin: MQTT ingestion, TimescaleDB, SoC/SoH estimation, anomaly detection, a Next.js dashboard and a read-only LLM assistant.

**Status:** in progress. Infrastructure setup (MQTT broker and TimescaleDB) is done. Simulator is publishing battery readings over MQTT. Ingestion service is consuming readings and saving them to TimescaleDB (Phase 1 complete).

## Quick start (so far)

1. Copy `.env.example` to `.env` and set a password.
2. Run `docker compose up -d`.

This starts a Mosquitto MQTT broker on port 1883 and a TimescaleDB database on port 5432.

## Simulator

`simulator/simulate.py` publishes a simulated battery reading (voltage, current, temperature) to the `battery/cell1/telemetry` MQTT topic once per second.

Run it with:python simulator/simulate.py

## Ingestion

`ingestion/ingest.py` subscribes to `battery/+/telemetry`, validates each reading with Pydantic, and inserts it into the `readings` hypertable in TimescaleDB.

Run it with:$env:POSTGRES_PASSWORD = "your_password"
python ingestion/ingest.py

Note: all data is simulated. This is a demonstrator, not a production system.
## Twin
`twin/twin.py` reads new readings, estimates state of charge (SoC) using Coulomb counting, and saves the result to `twin_state`.

Run it with:$env:POSTGRES_PASSWORD = "your_password"
python ingestion/ingest.py
It also computes the expected voltage from a simple battery model and saves it alongside SoC.
It also computes the residual (measured minus expected voltage) and raises an alert when the residual exceeds 0.1V.
The simulator supports fault injection (press Enter while it's running) to simulate a 10-second overheating and voltage-drop event, which the twin correctly detects and flags as alerts.
