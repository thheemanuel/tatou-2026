
import json
import logging

from pathlib import Path

from sqlalchemy import text



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

    
    assert "link" not in event
    assert "secret" not in event



def insert_version(db_engine, link, path):
    with db_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO Versions (link, path)
                VALUES (:link, :path)
            """),
            {
                "link": link,
                "path": str(path),
            },
        )


def test_secret_link_success(client, db_engine, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

    insert_version(db_engine, "valid-test-link", pdf_path)

    response = client.get("/api/get-version/valid-test-link")

    assert response.status_code == 200

    assert_secret_link_event(
        secret_link_events(caplog),
        "success",
    )


def test_secret_link_invalid(client, db_engine, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    response = client.get("/api/get-version/unknown-test-link")

    assert response.status_code == 404

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "invalid_link",
    )


def test_secret_link_database_error(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    
    from server import app

    original_engine = app.config.get("_ENGINE")

    try:
        app.config["_ENGINE"] = None

        response = client.get("/api/get-version/database-test-link")

    finally:
        if original_engine is None:
            app.config.pop("_ENGINE", None)
        else:
            app.config["_ENGINE"] = original_engine

    assert response.status_code == 503

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "database_error",
    )


def test_secret_link_invalid_file_path(client, db_engine, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

   
    outside_path = tmp_path.parent / "outside.pdf"

    insert_version(db_engine, "outside-test-link", outside_path)

    response = client.get("/api/get-version/outside-test-link")

    assert response.status_code == 500

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "invalid_file_path",
    )


def test_secret_link_file_missing(client, db_engine, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

   
    missing_path = tmp_path / "missing.pdf"

    insert_version(db_engine, "missing-test-link", missing_path)

    response = client.get("/api/get-version/missing-test-link")

    assert response.status_code == 410

    assert_secret_link_event(
        secret_link_events(caplog),
        "failure",
        "file_missing",
    )
