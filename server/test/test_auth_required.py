# Checks that every route that needs login rejects requests without a valid token.
# Mutation testing showed that removing @require_auth from five of these routes
# was not caught by any test, so this test is there to catch that.
import pytest
from itsdangerous import URLSafeTimedSerializer

from conftest import auth_header
from server import app

PROTECTED = [
    ("POST", "/api/upload-document"),
    ("GET", "/api/list-documents"),
    ("GET", "/api/list-versions"),
    ("GET", "/api/list-versions/1"),
    ("GET", "/api/list-all-versions"),
    ("GET", "/api/get-document"),
    ("GET", "/api/get-document/1"),
    ("DELETE", "/api/delete-document/1"),
    ("POST", "/api/delete-document"),
    ("POST", "/api/create-watermark"),
    ("POST", "/api/create-watermark/1"),
    ("POST", "/api/load-plugin"),
    ("POST", "/api/read-watermark"),
    ("POST", "/api/read-watermark/1"),
]
IDS = [f"{m} {p}" for m, p in PROTECTED]


def _forged_header():
    serializer = URLSafeTimedSerializer("not-the-server-key", salt="tatou-auth")
    return {"Authorization": "Bearer " + serializer.dumps({"uid": 1, "login": "alice"})}


@pytest.mark.parametrize("headers", [
    {},
    {"Authorization": "Basic YWxpY2U6cHc="},
    {"Authorization": "Bearer not-a-token"},
    "forged",
], ids=["missing", "wrong-scheme", "garbage", "forged-signature"])
@pytest.mark.parametrize("method,path", PROTECTED, ids=IDS)
def test_protected_route_rejects_bad_token(client, db_engine, method, path, headers):
    if headers == "forged":
        headers = _forged_header()
    resp = client.open(path, method=method, headers=headers)
    assert resp.status_code == 401
    assert "error" in resp.get_json()


@pytest.mark.parametrize("method,path", PROTECTED, ids=IDS)
def test_protected_route_rejects_expired_token(client, db_engine, method, path, monkeypatch):
    monkeypatch.setitem(app.config, "TOKEN_TTL_SECONDS", -1)
    resp = client.open(path, method=method, headers=auth_header(1, "alice"))
    assert resp.status_code == 401
    assert resp.get_json() == {"error": "Token expired"}


def test_valid_token_is_accepted(client, db_engine):
    resp = client.get("/api/list-documents", headers=auth_header(1, "alice"))
    assert resp.status_code == 200
    assert resp.get_json() == {"documents": []}
