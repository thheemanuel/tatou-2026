import os

import pytest
import rmap
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import create_engine, text


# create_app() runs at import and needs RMAP env vars + real GPG keys.
# Tests don't exercise RMAP, so give it dummy config and a no-op server.
class _StubRMAPServer:
    def __init__(self, *args, **kwargs):
        pass

    def loadIdentities(self, *args, **kwargs):
        pass


for _key, _value in {
    "RMAP_SERVER_PUB": "unused.asc",
    "RMAP_SERVER_PRIV": "unused.asc",
    "RMAP_CLIENT_KEYS": "unused",
    "RMAP_PRIVATE_KEY_PASSPHRASE": "unused",
    "RMAP_DOCUMENT_ID": "0",
    "RMAP_WATERMARK_KEY": "unused",
}.items():
    os.environ.setdefault(_key, _value)
rmap.RMAPServer = _StubRMAPServer

from server import app  # noqa: E402  (must come after the RMAP stub)


# Flask test client, with TESTING on so route errors raise instead of 500ing.
@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Adding in a way to turn off the rate limiting for testing purposes
    # The reason for this is because our own tests may send lots of requests, for example the Fuzzing
    app.config["RATE_LIMIT_ENABLED"] = False
    return app.test_client()


# In-memory SQLite standing in for MySQL, torn down after each test.
@pytest.fixture
def db_engine(tmp_path):
    app.config["STORAGE_DIR"] = tmp_path
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE Documents (
                id INTEGER PRIMARY KEY,
                name TEXT, path TEXT, ownerid INTEGER,
                creation TEXT, sha256 BLOB, size INTEGER
            )
        """))
    app.config["_ENGINE"] = engine
    yield engine
    app.config.pop("_ENGINE", None)


# Builds a valid Bearer token for the given user, signed with the app's real key.
def auth_header(uid, login):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="tatou-auth")
    token = serializer.dumps({"uid": uid, "login": login, "email": f"{login}@example.com"})
    return {"Authorization": f"Bearer {token}"}
