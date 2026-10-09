
# io module provides tools for working with data streams
# for example simulate files without creating one on your computer
import io
import json
import logging

from server import app

# mocking framework
# mocking means temporarily replacing a real dependency with a fake one during a test
from unittest.mock import patch

from conftest import auth_header

# collect all of the logs containing document.upload
# loops through all the events and collects the relevant ones
def upload_events(caplog):
    
    events = []

    for record in caplog.records:
        if record.name != "tatou.security":
            continue

        event = json.loads(record.message)

        if event.get("event") == "document.upload":
            events.append(event)

    return events


# testing uploading without a file
def test_missing_file_is_logged(client, caplog):
    
    #capture security logs
    caplog.set_level(logging.INFO, logger="tatou.security")

    # send an upload request without a file
    response = client.post(
        "/api/upload-document",
        headers=auth_header(1, "alice"),
        data={},
    )

    # verify the response
    assert response.status_code == 400

    # verify the security event
    events = upload_events(caplog)

    assert len(events) == 1
    assert events[0]["user_id"] == 1
    assert events[0]["result"] == "failure"
    assert events[0]["reason"] == "missing_file"
    assert len(events[0]["request_id"]) == 32

# testing uploading an invalid pdf
def test_invalid_pdf_is_logged(client, caplog):
    
    # capture the security logs
    caplog.set_level(logging.INFO, logger="tatou.security")

    # create a fake file
    # create an in-memory file containing "This is not a pdf"
    # so the contents of the file is not pdf data
    response = client.post(
        "/api/upload-document",
        headers=auth_header(1, "alice"),
        data={
            
            # flasks test client understands this as an uploaded file with two pieces of information:
            # the first item is the file-like object containing the bytes
            # the second item is the filename 
            
            "file": (
                io.BytesIO(b"This is not a PDF"),
                "invalid.pdf",
            )
        },
        
        # this tells the client to send the request as a multipart form submission
        
        # multipart form data is commonly used when uploading files over http
        
        # the request is conceptually equivalent to submitting a form containing a file input
        
        content_type="multipart/form-data",
    )

    # check that the file is rejected
    assert response.status_code == 400

    # check the security event
    events = upload_events(caplog)

    assert len(events) == 1
    assert events[0]["user_id"] == 1
    assert events[0]["result"] == "failure"
    assert events[0]["reason"] == "invalid_pdf"

    # check that the file contents werent logged
    
    # this is an important security assertion because if a user uploads a confidential document you do not wnat the contents to accidentally come up in the logs
    assert "This is not a PDF" not in caplog.text


# successfully uploading a document, test
def test_successful_upload_is_logged(client, tmp_path, caplog):
    
    # capture the security logs
    caplog.set_level(logging.INFO, logger="tatou.security")

    # we do not want the test uploads to appear in your applications real storage
    
    # so we replace it with pytests temporary directory
    
    original_storage = app.config["STORAGE_DIR"]
    app.config["STORAGE_DIR"] = tmp_path # creates a temporary filesystem directory

        # creates a fake database row
        
        # provide predetermined values instead of a real database row
    class FakeRow:
        id = 15
        name = "test.pdf"
        creation = "2026-10-09"
        sha256_hex = "abc123"
        size = 24

        # simulate the result of a sqlalchemy query
        # scalar() retrieves a single value from a database result
    class FakeResult:
        def scalar(self):
            return 15
        # when the application asks for a database result, the fake object supplies predictable data -> fake row
        def one(self):
            return FakeRow()

        # simulates a database connection, return fake result
    class FakeConnection:
        def execute(self, statement, params=None):
            return FakeResult()

        # simulate a database transaction context manager
        # with block
    class FakeTransaction:
        
        # returns fake connection
        def __enter__(self):
            return FakeConnection()

        # arguments describe any exception that occurred inside the block
        
        # returning false means exceptions should not be supressed
        
        # so this fake transaction behaves enough like a context manager for the application to use it
        def __exit__(self, exc_type, exc_value, traceback):
            return False

        # simulates a sqlalchemy database engine
        
        # fake engine -> fake transaction -> fake connection -> fake result
    class FakeEngine:
        def begin(self):
            return FakeTransaction()

    # create the pdf payload
    
    # small pdf-like byte sequence with pdf header etc
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

    # temporarily replace the real database engine
    
    try:
        #temporarily changes the flask configuration dictionary
        # returns the fake engine object
        # if get_engine() reads this configuration key, it will use the fake engine instead of the real database engine
        with patch.dict(app.config, {"_ENGINE": FakeEngine()}):
            response = client.post(
                "/api/upload-document",
                headers=auth_header(1, "alice"),
                data={
                    "file": (
                        io.BytesIO(pdf_bytes),
                        "test.pdf",
                    )
                },
                content_type="multipart/form-data",
            )
    finally:
        
        # ensure that the applications storage directory configuration gets restored, without this, a failed test might leave the application pointing at the temporary upload directory
        app.config["STORAGE_DIR"] = original_storage

    # verify successful response
    assert response.status_code == 201

    # verify the successful upload event
    events = upload_events(caplog)

    assert len(events) == 1
    assert events[0]["user_id"] == 1
    assert events[0]["document_id"] == 15
    assert events[0]["result"] == "success"
    assert events[0]["file_size"] == 24

    # check that filenames and contents are not logged
    assert "test.pdf" not in caplog.text
    assert "%PDF-1.4" not in caplog.text
