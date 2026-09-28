# I will be testing the check Gustav did by hand on our server.
# I have made this into an automated test instead of a manual one so that we can run it again anythime,
# and notice if the check breaks.

# It uses Gustavs conftest.py for the test database and login. Here is what it does:
    # Test 1: Alice gets her own document. This should pass through the test since it is her document.
    # Test 2: Bob tries to get Alices document. This should be blocked and recieve a 404 error.

from sqlalchemy import text
from conftest import auth_header


PDF_BYTES = b"%PDF-1.4\n%alice's secret manuscript\n%%EOF\n"

# This was inspired by the guest lecture by the professor from RISE.
# Bob and Alice are making sure who owns and who is asking for the document
ALICE = {"uid": 1, "login": "alice"}
BOB = {"uid": 2, "login": "bob"}

# Saves a real PDF file for Alice and adds a matching database row, bypassing the upload route.
# get-document only serves files that really exist inside STORAGE_DIR, so the file must be on disk.
def _seed_alice_document(db_engine, tmp_path):
    pdf_path = tmp_path / "alice.pdf"
    pdf_path.write_bytes(PDF_BYTES)
    with db_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO Documents (name, path, ownerid, creation, sha256, size) "
                "VALUES ('alice.pdf', :path, :ownerid, '2026-01-01', x'00', :size)"
            ),
            {"path": str(pdf_path), "ownerid": ALICE["uid"], "size": len(PDF_BYTES)},
        )

# Control: the owner can fetch her own document and gets exactly her file back.
# Without this, a 404 for Bob could just mean the route is broken.
def test_owner_can_get_their_own_document(client, db_engine, tmp_path):
    _seed_alice_document(db_engine, tmp_path)
    resp = client.get("/api/get-document/1", headers=auth_header(**ALICE))
    assert resp.status_code == 200
    assert resp.data == PDF_BYTES

# IDOR regression: another logged in user must not get someone else's document.
def test_other_user_cannot_get_someone_elses_document(client, db_engine, tmp_path):
    _seed_alice_document(db_engine, tmp_path)
    resp = client.get("/api/get-document/1", headers=auth_header(**BOB))
    assert resp.status_code == 404
    assert PDF_BYTES not in resp.data