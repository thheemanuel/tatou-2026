# Creating a fuzz test for my own watermarking method (Tom' authorfieldwatermarking) to test it against random inputs.
# Reason as to why I choose this is becuase I am familiar withthe code and what it does, and I want to make sure that it is robust against random inputs.
#  I also want to make sure that it is not possible to break the watermarking method by using random inputs.
# Using the tool hypothesis will allow me to generate a big amount of random inputs and test the watermarking method against them.

import fitz  # PyMuPDF
from hypothesis import example, given, settings, strategies as st

# Import from my watermarking method
from watermarking_method_tom import AuthorFieldWaterMarking


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