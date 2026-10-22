import pytest
from pydantic import ValidationError

from ingestion.ingest import Reading


def test_valid_reading_is_accepted():
    reading = Reading(
        cell_id="cell1",
        ts="2026-10-22T10:00:00+00:00",
        voltage=3.9,
        current=-2.0,
        temperature=25.0,
    )
    assert reading.cell_id == "cell1"
    assert reading.voltage == 3.9


def test_missing_field_is_rejected():
    with pytest.raises(ValidationError):
        Reading(
            cell_id="cell1",
            ts="2026-10-22T10:00:00+00:00",
            voltage=3.9,
            current=-2.0,
            # temperature is missing
        )


def test_non_numeric_voltage_is_rejected():
    with pytest.raises(ValidationError):
        Reading(
            cell_id="cell1",
            ts="2026-10-22T10:00:00+00:00",
            voltage="not-a-number",
            current=-2.0,
            temperature=25.0,
        )