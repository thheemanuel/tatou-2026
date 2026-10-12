# Creating a fuzz test for my own watermarking method (Tom' authorfieldwatermarking) to test it against random inputs.
# Reason as to why I choose this is becuase I am familiar withthe code and what it does, and I want to make sure that it is robust against random inputs.
#  I also want to make sure that it is not possible to break the watermarking method by using random inputs.
# Using the tool hypothesis will allow me to generate a big amount of random inputs and test the watermarking method against them.

# This file contains 2 fuzz testsfor my watermarking method, each has its own rule:
# 1. test_fuzz_roundtrip_any_secret_and_key.
    # Add a watermark, read it back with the same key and get the same secret. This covers PDFs that this method has written.
    
# 2. test_fuzz_read_any_author_field.
    # An attacker writes any text into the author field of a PDF, and read-secret may only refuse with SecretNotFoundError or InvalidKeyError
    # Anything else would result in a crash. This will cover PDFs that a user uploads.

import fitz  # PyMuPDF
from hypothesis import example, given, settings, strategies as st

# Import from my watermarking method
from watermarking_method_tom import AuthorFieldWaterMarking

# Import from watermarking method. Only these 2 errors are allowed to raise on bad inputs
from watermarking_method import InvalidKeyError, SecretNotFoundError

# This sequence is for when tatou writes the watermark and then read it back for us. Creating the information for the pdf and watermark
# also what to look for and what is allowed to be included
def make_pdf() -> bytes:
    # A small real PDF with one page of text, created once and reused for every example
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Fuzzing test document")
    data = doc.tobytes()
    doc.close()
    return data

PDF = make_pdf()
wm = AuthorFieldWaterMarking()

# The property (the rule that must always be true):
# whatever secret and key we use, reading the watermark back with the same key
# must give back exactly the same secret.
# We also make sure to always include atleast 1 character in the secret and key since no characters is already protected against in the
# watermarking method.
@example(secret="\x1f", key="0")                                # This bug was found when fuzzing: control characters.
@example(secret="a\xa0b", key="0")                              # Same bug with a realistic no-break space character.
@settings(max_examples=500, deadline=None)
@given(secret=st.text(min_size=1), key=st.text(min_size=1))
def test_fuzz_roundtrip_any_secret_and_key(secret, key):
    out = wm.add_watermark(PDF, secret=secret, key=key)
    assert wm.read_secret(out, key=key) == secret
    
    
    
def make_pdf_with_author(author: str) -> bytes:
    # A PDF where an attacker has written their own text into the author field
    # This sequence is needed in order to test the watermarking on pdfs uploaded by users
    doc = fitz.open()
    doc.new_page()
    doc.set_metadata({"author": author})
    data = doc.tobytes()
    doc.close()
    return data

# The property of this method is whatever an attacker writes into the author field of the pdf, read_secret will only answer
# with two errors that mean that there is no watermark or that the key is wrong or tampered with.
# If there is another error for example TypeError, it means that the method crashes on input it does not expect
@example(author="x|\u00e9")                                     # bug found by fuzzing: non-ASCII characters after "|"
@settings(max_examples=500, deadline=None)
@given(author=st.text())
def test_fuzz_read_secret_any_author_field(author):
    pdf = make_pdf_with_author(author)
    try:
        wm.read_secret(pdf, key="unit-test-key")
    except (SecretNotFoundError, InvalidKeyError):
        pass                                                    # The expected outcome, the method correctly refuses the fake value
    
# What is not covered in these tests: The subject field. read-secret falls back to it when the author field is empty. But test 2 only 
# fills in the author field. PDFs with their metadata stripped are not covered either.