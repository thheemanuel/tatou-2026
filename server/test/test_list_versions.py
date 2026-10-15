# Tests for /api/list-versions and /api/list-all-versions.
# These routes had no tests at all before. Both should only show versions of
# documents the logged in user owns, and list-all-versions should not show the
# secrets.
import pytest
from sqlalchemy import text

from conftest import auth_header

ALICE = auth_header(1, "alice")
BOB = auth_header(2, "bob")


# conftest only creates the Documents table, these routes also need Users and
# Versions. Alice owns documents 1 and 2, Bob owns document 3.
@pytest.fixture
def versions_db(db_engine):
    with db_engine.begin() as conn:
        conn.execute(text("CREATE TABLE Users (id INTEGER PRIMARY KEY, email TEXT, hpassword TEXT, login TEXT)"))
        conn.execute(text("""
            CREATE TABLE Versions (
                id INTEGER PRIMARY KEY, documentid INTEGER, link TEXT, intended_for TEXT,
                secret TEXT, method TEXT, position TEXT, path TEXT
            )
        """))
        conn.execute(text("INSERT INTO Users (id, email, hpassword, login) VALUES "
                          "(1, 'alice@example.com', 'x', 'alice'), (2, 'bob@example.com', 'x', 'bob')"))
        conn.execute(text("INSERT INTO Documents (id, name, path, ownerid) VALUES "
                          "(1, 'a1.pdf', 'a1.pdf', 1), (2, 'a2.pdf', 'a2.pdf', 1), (3, 'b1.pdf', 'b1.pdf', 2)"))
        conn.execute(text("""
            INSERT INTO Versions (id, documentid, link, intended_for, secret, method) VALUES
                (1, 1, 'link-1', 'group-07', 'secret-1', 'invisible-text'),
                (2, 1, 'link-2', 'group-08', 'secret-2', 'tom-author-field'),
                (3, 2, 'link-3', 'group-09', 'secret-3', 'theo_group21'),
                (4, 3, 'link-4', 'group-10', 'secret-4', 'invisible-text')
        """))
    return db_engine


# ---------------- list-versions ----------------

def test_list_versions_of_own_document(client, versions_db):
    resp = client.get("/api/list-versions/1", headers=ALICE)
    assert resp.status_code == 200
    versions = sorted(resp.get_json()["versions"], key=lambda v: v["id"])
    assert versions == [
        {"id": 1, "documentid": 1, "link": "link-1", "intended_for": "group-07",
         "secret": "secret-1", "method": "invisible-text"},
        {"id": 2, "documentid": 1, "link": "link-2", "intended_for": "group-08",
         "secret": "secret-2", "method": "tom-author-field"},
    ]


# the id can also be given as ?id= or ?documentid=
@pytest.mark.parametrize("query", ["id=1", "documentid=1"])
def test_list_versions_id_in_query(client, versions_db, query):
    resp = client.get(f"/api/list-versions?{query}", headers=ALICE)
    assert resp.status_code == 200
    assert sorted(v["id"] for v in resp.get_json()["versions"]) == [1, 2]


@pytest.mark.parametrize("url", ["/api/list-versions", "/api/list-versions?id=abc"])
def test_list_versions_needs_valid_id(client, versions_db, url):
    resp = client.get(url, headers=ALICE)
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "document id required"}


# Bob must not see the versions (and secrets) of Alice's document
def test_list_versions_of_other_users_document_is_empty(client, versions_db):
    resp = client.get("/api/list-versions/1", headers=BOB)
    assert resp.status_code == 200
    assert resp.get_json() == {"versions": []}


def test_list_versions_of_unknown_document_is_empty(client, versions_db):
    resp = client.get("/api/list-versions/99", headers=ALICE)
    assert resp.status_code == 200
    assert resp.get_json() == {"versions": []}


def test_list_versions_database_error(client, versions_db):
    with versions_db.begin() as conn:
        conn.execute(text("DROP TABLE Versions"))
    resp = client.get("/api/list-versions/1", headers=ALICE)
    assert resp.status_code == 503


# ---------------- list-all-versions ----------------

def test_list_all_versions_only_own_documents(client, versions_db):
    resp = client.get("/api/list-all-versions", headers=ALICE)
    assert resp.status_code == 200
    versions = resp.get_json()["versions"]
    assert sorted(v["id"] for v in versions) == [1, 2, 3]
    assert sorted(v["documentid"] for v in versions) == [1, 1, 2]


def test_list_all_versions_other_user(client, versions_db):
    resp = client.get("/api/list-all-versions", headers=BOB)
    assert resp.status_code == 200
    assert resp.get_json() == {"versions": [
        {"id": 4, "documentid": 3, "link": "link-4", "intended_for": "group-10", "method": "invisible-text"},
    ]}


# unlike list-versions, this route should not return the secrets
def test_list_all_versions_does_not_show_secrets(client, versions_db):
    versions = client.get("/api/list-all-versions", headers=ALICE).get_json()["versions"]
    assert versions
    assert all("secret" not in v for v in versions)


def test_list_all_versions_database_error(client, versions_db):
    with versions_db.begin() as conn:
        conn.execute(text("DROP TABLE Versions"))
    resp = client.get("/api/list-all-versions", headers=ALICE)
    assert resp.status_code == 503
