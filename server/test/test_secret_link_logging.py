
import json
import logging

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from server import app


def secret_link_events(caplog):
    events = []

    for record in caplog.records:
        if record.name != "tatou.security":
            continue

        event = json.loads(record.getMessage())

        if event.get("event") == "secret_link.access":
            events.append(event)

    return events


def assert_secret_link_event(events, result, reason=None):
    assert len(events) == 1

    event = events[0]

    assert event["result"] == result
    assert len(event["request_id"]) == 32
    assert event["source_ip"] == "127.0.0.1"
    assert "timestamp" in event

    if reason is not None:
        assert event["reason"] == reason
    else:
        assert "reason" not in event

    assert "link" not in event
    assert "secret" not in event



def fake_database_row(row):
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.first.return_value = row
    return engine


def request_with_engine(client, link, engine):
    original_engine = app.config.get("_ENGINE")

    try:
        app.config["_ENGINE"] = engine

        return client.get(f"/api/get-version/{link}")

    finally:
        if original_engine is None:
            app.config.pop("_ENGINE", None)
        else:
            app.config["_ENGINE"] = original_engine


def test_secret_link_success(client, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

    original_storage = app.config["STORAGE_DIR"]

    try:
        app.config["STORAGE_DIR"] = tmp_path

        row = SimpleNamespace(
            path=str(pdf_path),
            link="valid-test-link",
        )

        engine = fake_database_row(row)

        response = request_with_engine(
            client,
            "valid-test-link",
            engine,
        )

    finally:
        app.config["STORAGE_DIR"] = original_storage

    assert response.status_code == 200

    assert_secret_link_event(
        secret_link_events(caplog),
        "success",
    )


def test_secret_link_invalid(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    engine = fake_database_row(None)

    response = request_with_engine(
        client,
        "unknown-test-link",
        engine,
    )

    assert response.status_code == 404

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "invalid_link",
    )


def test_secret_link_database_error(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    engine = MagicMock()

    engine.connect.side_effect = RuntimeError("test database error")

    response = request_with_engine(
        client,
        "database-test-link",
        engine,
    )

    assert response.status_code == 503

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "database_error",
    )


def test_secret_link_invalid_file_path(client, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    outside_path = tmp_path / "outside.pdf"

    row = SimpleNamespace(
        path=str(outside_path),
        link="outside-test-link",
    )

    engine = fake_database_row(row)

    original_storage = app.config["STORAGE_DIR"]

    try:
        app.config["STORAGE_DIR"] = storage_dir

        response = request_with_engine(
            client,
            "outside-test-link",
            engine,
        )

    finally:
        app.config["STORAGE_DIR"] = original_storage

    assert response.status_code == 500

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "invalid_file_path",
    )


def test_secret_link_file_missing(client, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    missing_path = tmp_path / "missing.pdf"

    row = SimpleNamespace(
        path=str(missing_path),
        link="missing-test-link",
    )

    engine = fake_database_row(row)

    original_storage = app.config["STORAGE_DIR"]

    try:
        app.config["STORAGE_DIR"] = tmp_path

        response = request_with_engine(
            client,
            "missing-test-link",
            engine,
        )

    finally:
        app.config["STORAGE_DIR"] = original_storage

    assert response.status_code == 410

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "file_missing",
    )
