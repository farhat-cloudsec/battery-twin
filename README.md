# Battery Digital Twin

Simulated battery digital twin: MQTT ingestion, TimescaleDB, SoC/SoH estimation, anomaly detection, a Next.js dashboard and a read-only LLM assistant.

**Status:** in progress. Infrastructure setup (MQTT broker and TimescaleDB) is done.

## Quick start (so far)

1. Copy `.env.example` to `.env` and set a password.
2. Run `docker compose up -d`.

This starts a Mosquitto MQTT broker on port 1883 and a TimescaleDB database on port 5432.

Note: all data is simulated. This is a demonstrator, not a production system.

**Status:** in progress. Infrastructure setup (MQTT broker and TimescaleDB) is done. Simulator is publishing battery readings over MQTT.

## Simulator

`simulator/simulate.py` publishes a simulated battery reading (voltage, current, temperature) to the `battery/cell1/telemetry` MQTT topic once per second.


**Status:** in progress. Infrastructure setup (MQTT broker and TimescaleDB) is done. Simulator is publishing battery readings over MQTT. Ingestion service is consuming readings and saving them to TimescaleDB (Phase 1 complete).

## Ingestion

`ingestion/ingest.py` subscribes to `battery/+/telemetry`, validates each reading with Pydantic, and inserts it into the `readings` hypertable in TimescaleDB.

Run it with:
$env:POSTGRES_PASSWORD = "twin2026"
python ingestion/ingest.py
