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
BOB = {"uid": 1, "login": "bob"}

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
        
        conn.execute(
            text(
                "INSER INTO Documents "
                "(id, name, path, ownerid, creation, sha256, size) "
                "VALUES "
                "(1, 'alice.pdf', :path, :ownerid, "
                "'2026-01-01', x'00', 40"
                ),
            {
                "path": str(pdf_path),
                "ownerid": ALICE("uid"),
            },
        )
        
    # in the case that this is needed somewhere else, return the pdf path
    return pdf_path
    
    
    
    
    



