#imports 
# convert json strings into dictionaries
import json
# pythons built in logging system
import logging


# caplog captures logging messages produced while test runs.

# caplog is automatically provided by pytest

def security_records(caplog):
    
    # create an empty list where we will store the security events
    records = []
    
    
    # loops through all capotured log records
    for record in caplog.records:
        
        # filter out records that does not belong to the specialization D logger
        
        # skip the current iteration and move on to the next record if it doesnt match
        if record.name != "tatou.security":
            continue
        
        # stitches together a lot of things
        
        # 1. gets the text of the log message
        
        # 2. converts the json string into a python dictionary
        
        # 3. add the dictionary to the list
        
        records.append(json.loads(record.getMessage()))
        
    return records


    # pytest should automatically find functions with names starting with test
    
    # this is the actual test
    
    # client, simulating http request without starting a real server, from flask.
def test_missing_authorization_is_logged(client, caplog):
    
    
    # tells pytest to capture messages at the info level and above from the security logger
    
    # for example, other functions use "security_logger.info(...)"
    
    # that info-level is where we want to capture messages
    
    caplog.set_level(logging.INFO, logger="tatou.security")
    
    # via client, simulate a http get request to the endpoint list-documents
    
    # tests a request to this endpoint without authorization and therefore the assert line below 
    
    response = client.get("/api/list-documents")
    
    # assert that the response is 401 "unauthorized"
    
    assert response.status_code == 401
    
    # call the previous helper function to record and collect the security event.
    
    events = security_records(caplog)
    
    # verify that at least one captured security log reports an authentication failure caused by a missing or invalid authorization header with the outcome marked as failure
    
    # "any" returns true if at least one item satisfies a condition
    # "and" means that all three conditions must be true for the same event.
    
    assert any(
        event["event"] == "authentication.failure"
        and event["reason"] == "missing_or_invalid_authorization_header"
        and event["outcome"] == "failure"
        for event in events
    )
    
    
    # next test, invalid token, and if it is logged
def test_invalid_token_is_logged(client, caplog):
    
    # as before, set the caplog level to info where the messages will be captured
    caplog.set_level(logging.INFO, logger="tatou.security")
    
    # create a fake and obviously invalid token
    fake_token = "invalid-token-123123"
    
    # use the test client to send a get request to the endpoint list-documents with the fake bearer token
    
    # f-string allows you to insert variables into strings.
    
    response = client.get(
        "/api/list-documents",
        headers={"Authorization": f"Bearer {fake_token}"}
    )
    
    # assert or check that the request is rejected
    
    # 401, as in the previous method, means "Unauthorized"
    
    assert response.status_code == 401
    
    # calls the helper function to collect or retrieve the security logs
    events = security_records(caplog)
    
    # check whether at least one security event reports an authentication failure with the reason invalid_token
    assert any(
        event["event"] == "authentication.failure"
        and event["reason"] == "invalid_token"
        for event in events
    )
    
    # preventing token leakage
    
    # caplog.text contains the captured log output as one large string
    
    # verify that the fake authentication token does not appear anywhere in the captured logs
    
    # if the token appears, the assertion fails.
    
    assert fake_token not in caplog.text


# a test checking if the assign_request_id function actually adds a request id to the different logs or requests

# the function, which this code below tests, should add a unique request id before flask processes each http request

def test_security_event_has_request_id(client, caplog):
    
    # as above, client simulates http requests
    # caplog captures log messages
    # set_level() 
    caplog.set_level(logging.INFO, logger="tatou.security")

    # make an unauthorized request 
    response = client.get("/api/list-documents")

    # should be rejected with 401 Unauthorized
    assert response.status_code == 401

    # retrieve the security events captured during the request
    events = security_records(caplog)

    # next() retrieves the next item from an iterator
    # here, it retrieves the first matching authentication failure event
    
    # the body:
    
    # the body goes through the events and produces only those where the event type equals "authentication.failure"
    # it skips the other ones, for example "request.started" or something
    event = next(
        event
        for event in events
        if event["event"] == "authentication.failure"
    )

    # check that the request id exists (key)
    assert "request_id" in event

    # check that the request id is a string (isinstance checks the type of the object)
    assert isinstance(event["request_id"], str)

    # check that uuid.uuid4().hex produces 32 hexadecimal characters
    assert len(event["request_id"]) == 32
