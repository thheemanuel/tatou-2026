# Created by Tom Ellström Johansson
# This is the second part of my fuzzing specialization where i will be fuzzing the tatou API through the flask test client.
# auth_header() from conftest.py gives us a valid user token, so the inputs will get past authentication and then reach the real code,
# instead of being stopped with a 401 error. The reason for this is because we want to test the real code and not the authentication.

# The oracle is that the response status code should never answer with a 500 error or crash on a bad input.
# So a clean 400 would be the correct response for a bad input. For example a 400 for a bad request and a 404 for a not found error.

# After the first testing we have now added in example
from hypothesis import HealthCheck, example, given, settings, strategies as st
from conftest import auth_header

# So here we fuzz the document id in the URL of delete-document.
# Example is added in to test a specific input that we found in the first round of fuzzing that caused a crash.
# Since we have now added in a fix for that we will see how the test handels it.
@example(document_id=":") 
@settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
# Adding in exclude_catergories=("Cs",) in to the @given() to exclude surrogate characters since they are not valid characters on their own and can not be built into a request.
@given(document_id=st.text(min_size=1, alphabet=st.characters(exclude_categories=("Cs",), exclude_characters="/?#%")))
def test_fuzz_delete_document_id(client, db_engine, document_id):
    response = client.delete(f"/api/delete-document/{document_id}", headers=auth_header(1, "alice"))
    assert response.status_code < 500


# During the first test we could see that there were errors on line 800 ish for document(id) in server.py aswell as another line.
# In the second test we can see that the example now passes but the fuzzing test fails when building and that server.py never appeared in the traceback.
# We will now need to figure out what is causing this error. The error message says that it is a surrogate character, when checking what that means it seems to 
# be half of a character code and isnt a valid character on its own. When thinking about this bug and from an adversaries perspective. I first though that an attacker might use this,
# but we can see in the output that the request was never built so an attacker will fortunately not be able to use this.

# So this was not really a bug in itself it was a test problem since the test created something that can not be built into a request. Perhaps we can leave out the surrogates then in some way.
# I added in exclude_categories=("Cs",) in the @given() parameter in order to exclude surrogate characters so that they can never be sent in a real http request.

# Overall results from testing 13/10
# Test 1:
#   Failed: The smallest input document.id=":" caused a crash in server.py. The fail was (doc.id = int(document.id)). Seen through a ValueError.
#   The request had first passed the @require_auth so a real logged in user could run into this bug.

#   Fix: I added in around document.id, try/except around the int() to catch ValueError and also added in TypeError so that if there was no document.id provided it would also be caught.
#   Now the bad ids get a 400 error and a message stating it has to be a real number.
#   Also added in a regression that would also specifically test the input document.id=":". @example(document_id=":").

# Test 2:
#   Failed: This fail was probably not a server bug but an actual test failure in the fuzzing test. There was an input for "\ud800" a surrogate. After looking up what that is. It is when there
#   is half of a character code and isnt a valid character on its own.

#   Fix: excluded "Cs" in the test structure: (exclude_categories=("Cs",) so now it does not take surrogate characters as input

# Test 3:
#   Passed: This one passed within 0.51s. We used 300 random requests plus the ":" example from the first failed test.