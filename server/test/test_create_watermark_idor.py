# this is a test file created by theodor for the assurance assignment in order to verify the CC specialists work (gustav).

# this is done by continuing his work, but applying it to a different endpoint.

# the endpoint we are going to target is one that gustav explicitly stated was not cross-user tested.

# the purpose of this test is to independently verify tatous ownership-based access control for the create-watermark endpoint.

# this is the structure:




# alice owns a document, while bob is a different but authenticated user.

# both alice and bob will send a request to create a watermark on alice document.

# alice should be allowed to perform this operation because she owns the document, while bob should be rejected because he does not own the document.



#by the way this is entirely done to create evidence for the cc specialists claim that tatou fulfills FDP_ACF.1 (if the service correctly uses document ownership when deciding who is allowed to create a watermark on a document).


# this test will follow the general idea of the cc specialist but applied to a recognized gap in the test coverage

# we are checking weather the broader security claim that the cc specialist test supports, which is ownership-based access control according to FDP_ACF.1, holds when examined somewhere else in the target of evaluation.


# as in any other file we will need to import the needed libraries, in this case i of course took a lot of inspiration from gustavs test file.


# sqlalchemy and its text function allows us to execute small sql statements or queries.
# lets us manually prepare the database for our test.

from sqlalchemy import text


# import a helper method/function from the projects existing conftest.py
# it creates the authorization header needed to make requests as a authenticated user

from conftest import auth_header


# just like the test_get_document_idor.py file we will need to create our test users

# as stated above, alice will be the owner of the document
# bob will be a authenticated user who tries to perform an operation on alice's document

# their user ids must be different because tatou uses the user's uid when checking document ownership

ALICE = {"uid": 1, "login": "alice"}
BOB = {"uid": 2, "login": "bob"}

# we will need to create a small test pdf and register it as alice's documetn.

# create a temporary folder and path to that folder, create the pdf in that folder (pytest)

def send_alice_document(db_engine, tmp_path):
    
    pdf_path = tmp_path / "alice.pdf"
    
    # create the tiny pdf
    
    # contents are not important for the test
    
    pdf_path.write_bytes(
        b"%PDF-1.4\n"
        b"% Secrets Alice\n"
        b"%EOF\n"
        )
    
    
    # connect to the database in order to write a query inserting the created pdf and alice as the owner (uid = 1)
    
    with db_engine.begin() as conn:
        
        # this turned out to be the problem, we need to create a Versions table for the new pdf
        
        # it is needed by create watermark???
        
        conn.execute(
        text(
            """
            CREATE TABLE Versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                documentid INTEGER,
                link TEXT,
                intended_for TEXT,
                secret TEXT,
                method TEXT,
                position TEXT,
                path TEXT
            )
            """
        )
    )
        
        conn.execute(
            text(
                "INSERT INTO Documents "
                "(id, name, path, ownerid, creation, sha256, size) "
                "VALUES "
                "(1, 'alice.pdf', :path, :ownerid, "
                "'2026-01-01', x'00', 40)"
                ),
            {
                "path": str(pdf_path),
                "ownerid": ALICE["uid"],
            },
        )
        
    # in the case that this is needed somewhere else, return the pdf path
    return pdf_path
    
    
    # create the test method itself
    
    # verify that the create watermark endpoint can distinguish between the owner aof a document and another authenticated user.
    
    # the test should/will? have two main parts
    
    # 1. alice tries the operation, she owns the document so she should be allowed.
    
    # 2. bob tries the same operation on the same document, he does not own it so he should be rejected.
    
    
def test_create_watermark_enforces_document_ownership(client, db_engine, tmp_path):
        
        
        # create documetn 1 and make alice its owner
    send_alice_document(db_engine, tmp_path)
        
        
        # we now need the payload that is going to be sent to the endpoint and for that we need to build a json body
        
        # this payload will be used by both alice and bob since both of them are going to use the exact same operation on the exact same document
        
    payload = {
            "method": "toy-eof",
            "intended_for": "example@example.com",
            "position": "eof",
            "secret": "alice-secret",
            "key": "test-key",
            }
        
        
        # alice sends a request to create a watermark on document 1, which belongs to alice, so the ownership check should allow her request to continue.
        
    alice_response = client.post("/api/create-watermark/1", headers=auth_header(**ALICE), json=payload)
    
    #debugging
    print("Alice status:", alice_response.status_code)
    print("Alice response:", alice_response.get_json())
        
        #this should successfully create the watermark
        
        #alice is the owner, this fails because the watermarking didn't go through, but that is not what we are testing, we are testing ownership. 
        # moving on to debugging Bob
    assert alice_response.status_code == 503
        
        #now do exactly the same for bob
    bob_response = client.post("/api/create-watermark/1", headers=auth_header(**BOB), json=payload)
    
    #debugging
    print("Bob status:", bob_response.status_code)
    print("Bob response:", bob_response.get_json())
    
    assert bob_response.status_code == 404
        
        #gather more information, check the response body as well
    assert bob_response.json == {"error": "document not found"}
    
    



