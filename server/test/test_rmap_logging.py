
import json
import logging

from unittest.mock import patch

import server

from server import RMAPServer


def rmap_events(caplog):
    
    events = []

    for record in caplog.records:
        if record.name != "tatou.security":
            continue

        event = json.loads(record.getMessage())

        if event.get("event") == "rmap.authentication":
            events.append(event)

    return events


def assert_rmap_event(events, stage, result, reason=None):
    assert len(events) == 1

    event = events[0]

    assert event["stage"] == stage
    assert event["result"] == result
    assert len(event["request_id"]) == 32
    assert event["source_ip"] == "127.0.0.1"
    assert "timestamp" in event

    if reason is not None:
        assert event["reason"] == reason


def test_initiate_invalid_format(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    response = client.post("/api/rmap-initiate", json={})

    assert response.status_code == 400

    assert_rmap_event(
        rmap_events(caplog),
        "initiate",
        "failure",
        "invalid_message_format",
    )


def test_get_link_invalid_format(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    response = client.post("/api/rmap-get-link", json={})

    assert response.status_code == 400

    assert_rmap_event(
        rmap_events(caplog),
        "get_link",
        "failure",
        "invalid_message_format",
    )


def test_initiate_success(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    with patch.object(
        RMAPServer,
        "receiveMsg1",
        return_value=("TestGroup", {"payload": "response"}),
        create=True
    ):
        response = client.post(
            "/api/rmap-initiate",
            json={"payload": "test"},
        )

    assert response.status_code == 200

    assert_rmap_event(
        rmap_events(caplog),
        "initiate",
        "success",
    )


def test_initiate_protocol_rejected(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    
    with patch.object(
        RMAPServer,
        "receiveMsg1",
        side_effect=ValueError("bad protocol message"),
        create=True
    ):
        response = client.post(
            "/api/rmap-initiate",
            json={"payload": "test"},
        )

    assert response.status_code == 400

    assert_rmap_event(
        rmap_events(caplog),
        "initiate",
        "failure",
        "unexpected_error",
    )


def test_get_link_protocol_rejected(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    with patch.object(
        RMAPServer,
        "receiveMsg2",
        side_effect=ValueError("bad protocol message"),
        create=True
    ):
        response = client.post(
            "/api/rmap-get-link",
            json={"payload": "test"},
        )

    assert response.status_code == 500

    assert_rmap_event(
        rmap_events(caplog),
        "get_link",
        "processing_failure",
        "watermark_or_storage_error",
    )


def test_get_link_duplicate_link(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    with patch.object(
        RMAPServer,
        "receiveMsg2",
        return_value=("TestGroup", "test-link", {"payload": "response"}),
        create=True
    ):
       
        response = client.post(
            "/api/rmap-get-link",
            json={"payload": "test"},
        )

    
    assert response.status_code in (409, 500)

    events = rmap_events(caplog)

    assert len(events) == 2
    assert events[0]["stage"] == "get_link"
    assert events[0]["result"] == "success"
    assert events[1]["stage"] == "get_link"
    assert events[1]["result"] == "processing_failure"
    assert events[1]["reason"] == "duplicate_link"


def test_get_link_unexpected_error(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    with patch.object(
        RMAPServer,
        "receiveMsg2",
        side_effect=RuntimeError("test error"),
    ):
        response = client.post(
            "/api/rmap-get-link",
            json={"payload": "test"},
        )

    assert response.status_code == 500

    assert_rmap_event(
        rmap_events(caplog),
        "get_link",
        "processing_failure",
        "watermark_or_storage_error",
    )
