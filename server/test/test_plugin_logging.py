
import json
import logging
import pickle

from conftest import auth_header


def plugin_events(caplog):
    
    events = []

    for record in caplog.records:
        if record.name != "tatou.security":
            continue

        event = json.loads(record.message)

        if event.get("event") == "plugin.load":
            events.append(event)

    return events


def test_missing_filename_is_logged(client, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    response = client.post(
        "/api/load-plugin",
        headers=auth_header(1, "alice"),
        json={},
    )

    assert response.status_code == 400

    events = plugin_events(caplog)

    assert len(events) == 1
    assert events[0]["user_id"] == 1
    assert events[0]["result"] == "failure"
    assert events[0]["reason"] == "missing_filename"
    assert len(events[0]["request_id"]) == 32


def test_invalid_extension_is_logged(client, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    from server import app

    original_storage = app.config["STORAGE_DIR"]
    app.config["STORAGE_DIR"] = tmp_path

    try:
        response = client.post(
            "/api/load-plugin",
            headers=auth_header(1, "alice"),
            json={"filename": "test.txt"},
        )
    finally:
        app.config["STORAGE_DIR"] = original_storage

    assert response.status_code == 400

    events = plugin_events(caplog)

    assert len(events) == 1
    assert events[0]["result"] == "failure"
    assert events[0]["reason"] == "invalid_extension"
    assert "test.txt" not in caplog.text


def test_missing_plugin_file_is_logged(client, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    from server import app

    original_storage = app.config["STORAGE_DIR"]
    app.config["STORAGE_DIR"] = tmp_path

    try:
        response = client.post(
            "/api/load-plugin",
            headers=auth_header(1, "alice"),
            json={"filename": "missing.pkl"},
        )
    finally:
        app.config["STORAGE_DIR"] = original_storage

    assert response.status_code == 404

    events = plugin_events(caplog)

    assert len(events) == 1
    assert events[0]["result"] == "failure"
    assert events[0]["reason"] == "file_not_found"
    assert "missing.pkl" not in caplog.text


def test_rejected_serialized_object_is_logged(client, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="tatou.security")

    from server import app

    original_storage = app.config["STORAGE_DIR"]
    app.config["STORAGE_DIR"] = tmp_path

    plugins_dir = tmp_path / "files" / "plugins"
    plugins_dir.mkdir(parents=True)

    # serialize a harmless built in object
    # safeunpickler should reject its class because it is not allowed
    plugin_path = plugins_dir / "rejected.pkl"
    plugin_path.write_bytes(pickle.dumps(ValueError("test")))

    try:
        response = client.post(
            "/api/load-plugin",
            headers=auth_header(1, "alice"),
            json={"filename": "rejected.pkl"},
        )
    finally:
        app.config["STORAGE_DIR"] = original_storage

    assert response.status_code == 400

    events = plugin_events(caplog)

    assert len(events) == 1
    assert events[0]["result"] == "failure"
    assert events[0]["reason"] == "forbidden_class"
    assert "rejected.pkl" not in caplog.text


def test_successful_plugin_load_is_logged(client, tmp_path, caplog, monkeypatch):
    caplog.set_level(logging.INFO, logger="tatou.security")

    import server
    from server import app

    original_storage = app.config["STORAGE_DIR"]
    app.config["STORAGE_DIR"] = tmp_path

    plugins_dir = tmp_path / "files" / "plugins"
    plugins_dir.mkdir(parents=True)

    plugin_path = plugins_dir / "valid.pkl"
    plugin_path.write_bytes(b"placeholder")

    class FakePlugin:
        name = "test-logging-plugin"

        def add_watermark(self):
            pass

        def read_secret(self):
            pass

    class FakeUnpickler:
        def __init__(self, file):
            pass

        def load(self):
            return FakePlugin

    # mock deserialization so this test checks the success logging path
    # without needing to build a real serialized plugin
    monkeypatch.setattr(server, "SafeUnpickler", FakeUnpickler)

    # make the interface check accept our test class
    monkeypatch.setattr(server, "WatermarkingMethod", None)

    original_methods = server.WMUtils.METHODS.copy()

    try:
        response = client.post(
            "/api/load-plugin",
            headers=auth_header(1, "alice"),
            json={"filename": "valid.pkl"},
        )
    finally:
        app.config["STORAGE_DIR"] = original_storage
        server.WMUtils.METHODS.clear()
        server.WMUtils.METHODS.update(original_methods)

    assert response.status_code == 201

    events = plugin_events(caplog)

    assert len(events) == 1
    assert events[0]["user_id"] == 1
    assert events[0]["result"] == "success"
    assert "valid.pkl" not in caplog.text
