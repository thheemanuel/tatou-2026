from sqlalchemy import text
from conftest import auth_header


# Inserts one document row owned by owner_id, bypassing the upload route.
def _seed_document(db_engine, owner_id):
    with db_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO Documents (name, path, ownerid, creation, sha256, size) "
                "VALUES ('doc.pdf', 'doc.pdf', :ownerid, '2026-01-01', x'00', 10)"
            ),
            {"ownerid": owner_id},
        )


# A document's owner can delete their own document.
def test_owner_can_delete_their_own_document(client, db_engine):
    _seed_document(db_engine, owner_id=1)
    resp = client.delete("/api/delete-document/1", headers=auth_header(uid=1, login="alice"))
    assert resp.status_code == 200
    assert resp.json["deleted"] is True


# IDOR regression: a different user must not be able to delete someone else's document.
def test_other_user_cannot_delete_someone_elses_document(client, db_engine):
    _seed_document(db_engine, owner_id=1)
    resp = client.delete("/api/delete-document/1", headers=auth_header(uid=2, login="mallory"))
    assert resp.status_code == 404
