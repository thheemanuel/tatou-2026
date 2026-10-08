import json
import logging

# text() allows you to write raw sql statements that sqlalchemy can execute.
from sqlalchemy import text

# importing the auth_header function that builds a valid bearer token for the given user, signed with the apps real key
from conftest import auth_header


def security_events(caplog):
    # create an empty list
    events = []

    # loop through the captured log records
    # keep only those from the "tatou.security" logger
    # convert their json messages into python dictionariesw
    for record in caplog.records:
        if record.name == "tatou.security":
            events.append(json.loads(record.message))

    return events


# bob tries to access alices document
def test_other_users_document_is_logged(client, db_engine, caplog):
    
    # document 15 belongs to alice (user 1).
    
    with db_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO Documents (id, name, path, ownerid, size)
                VALUES (15, 'alice.pdf', '/tmp/alice.pdf', 1, 100)
            """)
        )

    # bob (user 2) attempts to access alices document
    
    
    #capture security events
    caplog.set_level(logging.INFO, logger="tatou.security")

    # bob attempts to access alices document
    # simulate bob making a http request
    response = client.get(
        "/api/get-document/15",
        headers=auth_header(2, "bob"),
    )

    # check 404 not found response
    assert response.status_code == 404

    # extract the security event
    events = security_events(caplog)
    
    # using list comprehension, create a new list containing only events where the rule "if event["event"]...." applies
    denied = [
        event for event in events
        if event["event"] == "authorization.denied"
    ]

    # verify the logged information
    
    # len(denied) == 1 verifies that exactly one authorization denial event was logged
    
    # denied[0] retrieves the first event in the list
    
    # user_id == 2 bob attempted the acces
    # resource_id == 15 document 15 was requested
    # action == "read" bob attemted to read it
    # reason == "ownership_mismatch" bob isnt the owner
    assert len(denied) == 1
    assert denied[0]["user_id"] == 2
    assert denied[0]["resource_id"] == 15
    assert denied[0]["action"] == "read"
    assert denied[0]["reason"] == "ownership_mismatch"


    # A nonexistent document should not produce an ownship violation 

def test_nonexistent_document_is_not_logged_as_ownership_violation(
    client, db_engine, caplog
):
    # configure logging, same as before
    caplog.set_level(logging.INFO, logger="tatou.security")

    # request document 9999
    response = client.get(
        "/api/get-document/9999",
        headers=auth_header(2, "bob"),
    )

    # check the response, that it is 404
    assert response.status_code == 404

    # check that no ownership violation was logged
    events = security_events(caplog)

    # same as before, any() returns true if at least one item matches, but this time it is not:
    # verify that none of the captured security events is an authorization denial
    # what this poves:
    # requesting a nonexistent document doesnt incorrectly create an ownership-mismatch security event.
    assert not any(
        event["event"] == "authorization.denied"
        for event in events
    )

    # alice accesses her own document
    
def test_owner_access_is_not_logged_as_denied(
    client, db_engine, caplog, tmp_path
):
    # create a minimal temporary pdf for alice
    # 
    pdf_path = tmp_path / "alice.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj\n<<>>\nendobj\n"
        b"trailer\n<<>>\n%%EOF\n"
    )

    # insert the document into the database
    with db_engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO Documents (id, name, path, ownerid, size)
                VALUES (15, 'alice.pdf', :path, 1, 100)
            """),
            {"path": str(pdf_path)},
        )

    caplog.set_level(logging.INFO, logger="tatou.security")

    # alice requests her own document
    response = client.get(
        "/api/get-document/15",
        headers=auth_header(1, "alice"),
    )
    # check that the response is 200 (OK)
    # alice user id is 1 and the document also belongs to user with id of 1
    assert response.status_code == 200

    events = security_events(caplog)

    # verify that no denial event was logged
    assert not any(
        event["event"] == "authorization.denied"
        for event in events
    )