from server import app

# Using the db_engine fixture (SQLite) so healthz doesn't wait 4 seconds
# trying to connect to the real MySQL database.
def test_healthz_route(db_engine):
    client = app.test_client()
    resp = client.get("/healthz")

    assert resp.status_code == 200
    assert resp.is_json

