# Tests for the secret version links made by /api/create-watermark.
# The platform specification says the link "SHOULD not be guessable". The link
# used to be sha1("<name>__<recipient>.pdf"), which anyone can compute, and
# a second version for the same recipient got the same link and destroyed
# the first version's file. Now the link is random.
import hashlib
import re
import sqlite3
from pathlib import Path

import fitz
import pytest
from sqlalchemy import text

import watermarking_utils as WMUtils
from conftest import auth_header

ALICE = auth_header(1, "alice")
KEY = "test-key"


@pytest.fixture
def alice_document(db_engine, tmp_path, monkeypatch):
    # create-watermark uses LAST_INSERT_ID(), which is a MySQL function that
    # SQLite doesn't have, so add it to this test's database connection.
    with db_engine.connect() as conn:
        raw = conn.connection.driver_connection
        raw.create_function(
            "LAST_INSERT_ID", 0, lambda: raw.execute("SELECT last_insert_rowid()").fetchone()[0]
        )

    # The server passes the file path as a Path object. PyMySQL turns it into
    # text, SQLite doesn't, so tell sqlite to do the same (only during the test).
    monkeypatch.setitem(sqlite3.adapters, (type(Path()), sqlite3.PrepareProtocol), str)

    with db_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE Versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, documentid INTEGER, link TEXT UNIQUE,
                intended_for TEXT, secret TEXT, method TEXT, position TEXT, path TEXT
            )
        """))

    # a real one page pdf, owned by Alice
    pdf_path = tmp_path / "files" / "alice" / "report.pdf"
    pdf_path.parent.mkdir(parents=True)
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Alice's report")
    doc.save(pdf_path)
    doc.close()
    with db_engine.begin() as conn:
        conn.execute(
            text("INSERT INTO Documents (id, name, path, ownerid) VALUES (1, 'report.pdf', :path, 1)"),
            {"path": str(pdf_path)},
        )
    return pdf_path


def create_version(client, secret):
    body = {"method": "invisible-text", "intended_for": "bob@example.com", "secret": secret, "key": KEY}
    return client.post("/api/create-watermark/1", headers=ALICE, json=body)


def test_link_is_random_and_not_based_on_the_name(client, alice_document):
    resp = create_version(client, "for-bob")
    assert resp.status_code == 201
    link = resp.get_json()["link"]

    # same format as before: 40 hex characters
    assert re.fullmatch(r"[0-9a-f]{40}", link)
    # but not the old guessable value anymore
    old_guessable = hashlib.sha1(b"report__bobexample.com.pdf").hexdigest()
    assert link != old_guessable


def test_two_versions_for_same_recipient_get_different_links(client, alice_document):
    first = create_version(client, "first").get_json()
    second = create_version(client, "second").get_json()
    assert first["link"] != second["link"]
    assert first["filename"] != second["filename"]


# This used to return 410 Gone: the second version overwrote the first one's
# file and then deleted it when the database insert failed.
def test_second_version_does_not_destroy_the_first(client, alice_document):
    first = create_version(client, "first").get_json()
    assert create_version(client, "second").status_code == 201

    resp = client.get(f"/api/get-version/{first['link']}")
    assert resp.status_code == 200
    assert WMUtils.read_watermark("invisible-text", resp.data, key=KEY) == "first"


def test_unknown_link_is_not_found(client, alice_document):
    create_version(client, "for-bob")
    resp = client.get("/api/get-version/" + "0" * 40)
    assert resp.status_code == 404
