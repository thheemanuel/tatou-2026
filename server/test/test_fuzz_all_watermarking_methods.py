# This will be the next test of my fuzzing specialization where I will try to test all group members watermarking methods in one script
# It will be a simple test to see if we can find any bugs
# The reason as to why we do this shared test is because the current test_watermarking_all_methods skips three out of the four methods
# since its sample PDF has 0 pages. So the methods were never really tested with real input.
# So the oracle in this one adds in a watermark for each method and then reads it back with the same key
# It should give back the same secret, if it doesnt we know that the method is broken for that input

# First import PyMuPDF and other dependencies
import fitz
import pytest
from hypothesis import given, settings, strategies as st

# Importing all the watermark methods from the group members
from watermarking_method_tom import AuthorFieldWaterMarking
from watermarking_method_gustav import InvisibleTextWatermark
from watermarking_method_theo import watermarking_method_theo

def make_pdf() -> bytes:
    # Here we create a small PDF with one page of text. The reason behind this is because the methods
    # need atleast one page to work on.
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Fuzzing test document")
    data = doc.tobytes()
    doc.close()
    return data

# Createing a pdf with all the information we have inputted above. This is created ones and then reused for all methods, so we want the PDF bytes
PDF = make_pdf()

# Here we create one instance for each method. This means that pytest will run the test once for each method
ALLMETHODS = [AuthorFieldWaterMarking(), InvisibleTextWatermark(), watermarking_method_theo()]

# ids=lambda m: m.name will make pytest display the name of the method in the results
# max_examples=100. Keeping it to 100. The reason is because after discussing with Theo and Gustav, Theo explained that his method
# writes on every page which makes it slower. So I decided to keep it to 100 instead of 500 in this test.
# min_size=1 this is done because empty secrets and keys are already rejected on purpose already in the methods, 
# so that is already tested
# dealine.None is something I implemented after trying the first time since apparently Hypothesis has a time limit which it follows
# and it will fail if it takes longer then the time limit of around 200 ms. So this is just to make sure that it can take the time needed to create the PDFs 
@pytest.mark.parametrize("wm", ALLMETHODS, ids=lambda m: m.name)
@settings(max_examples=100, deadline=None)
@given(secret=st.text(min_size=1), key=st.text(min_size=1))
def test_fuzz_roundtrip_all_watermarking_methods(wm, secret, key):
    # Write out the watermark and then read it back to us in assert
    out = wm.add_watermark(PDF, secret=secret, key=key)
    assert wm.read_secret(out, key=key) == secret
    
# RESULTS FROM TESTING - 12/10
# During the test I did we had the results of 1 watermarking method passing and 2 failing.
#       Tom: passed
#       Gustav and Theos methods failed. The watermark seems to be written but when we read it back with the same key 
#       we get the wrong key error. In my own method I recieved a similar error (bug 1) but I have not confirmed reason for the fail in this test.

# The smallest failing inputs that we found in Hypothesis are:
#       theo_group21: secret="\x0b" a control character
#       And for Gustav: secret="\x7f" also a control character

# Why it fails: not confirmed yet. The test only shows that these two methods do not read back the same secret for these inputs.
# A possible reason is that the stored text is changed when the PDF is saved or read, as in my own method through PyMuPDF
# (see item #4 in watermarking_method_tom.py). Theo stores the secret in the PDF metadata and Gustav in the page text.

# So the effect this can have is that for these secrets a leaked PDF can not be traced and the error also blames the key.
# I have however not tested longer secrets, other unicode characters and also ofcourse PDFs with more than 1 page.
# The solution would be to first talk to Gustav and Theos about the bug found and find the cause for the bug. If the cause is the 
# same as in my own method then the fix could be to implement Base64 in these methods aswell. 