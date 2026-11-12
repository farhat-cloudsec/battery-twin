CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS readings (
  time TIMESTAMPTZ NOT NULL,
  cell_id TEXT NOT NULL,
  voltage DOUBLE PRECISION,
  current DOUBLE PRECISION,
  temperature DOUBLE PRECISION
);
SELECT create_hypertable('readings', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS readings_cell_time_idx ON readings (cell_id, time DESC);

CREATE TABLE IF NOT EXISTS twin_state (
  time TIMESTAMPTZ NOT NULL,
  cell_id TEXT NOT NULL,
  soc DOUBLE PRECISION,
  expected_voltage DOUBLE PRECISION,
  residual DOUBLE PRECISION,
  soh DOUBLE PRECISION
);
SELECT create_hypertable('twin_state', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  time TIMESTAMPTZ NOT NULL,
  cell_id TEXT NOT NULL,
  severity TEXT,
  message TEXT
);