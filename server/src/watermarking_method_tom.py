# Individual watermarking method for Tom Ellström Johansson
# The work is inspired by the add_after_eof.py and watermarking_method.py, github, AI, Stackoverflow, articles and other forums.

# --------------- For Nicolas -----------------
# I tested this in a test_watermarking that i created with AI. That was solely done to test my method and I have not pushed any of those changes into the repo for our project.
# If you would like to see the test I created with AI, I can send it to you.
# Some parts of this method is also something I recieved help with from both github, AI, Stackoverflow, articles, and classmates etc. I have worked a lot with the method
# and all of the implementations are things that I feel that I have understood myself before implementing.

# I will not update the groups test_watermarking_all_methods with my testing since that is not something I have discussed with the group. We will work on that
# for the next deadline.

# It is not perfect but I have spent quite some time on creating it so I still think that is quite good to me. I have also added comments down below on certain
# improvments that I would like to fix and implement in the future.
# -------------------------------

# Steps that I would like to implement in this method
# From research I have understood that a good watermarking method should include certain properties
# Hosny et al. 2024 (10.1016/j.cosrev.2024.100662) and Warhera et al. 2021 (https://arxiv.org/pdf/2207.06909)
    # 1. Imperceptibility: It should not visibly alter the document's appearance

    # 2. Safety and precaution: Making sure that there are some safety implementations
    # we do not want to execute unneccassary code if it is not needed

    # 3. Capacity: The amount of information embedded in a watermarked image also known as data payload

# These references are more structured for images/audio/video, but I still believe they provide good reasonings as to why I am using them for this watermarking method

# Improvements i would like to have implemented further on
    # Robustness: It should be able to clear PDF handling: opening/resaving in a viewer, printing into a pdf, edits
    # Secure: More security. This is probably the biggest problem and for forgeability: Cao et al. 2026 (https://arxiv.org/pdf/2510.02384)
    # And more

# Base is taken from add_after_eof.py
from __future__ import annotations
from typing import Final

import hmac
import hashlib
import fitz # PyMuPDF

from watermarking_method import(
    InvalidKeyError,
    SecretNotFoundError,
    WatermarkingError,
    WatermarkingMethod,

# Adding in PdfSource and load_pdf_bytes in order to check the size of the pdf
    PdfSource,
    load_pdf_bytes,
)

class AuthorFieldWaterMarking(WatermarkingMethod):
    # Unique name, the other codes uses this to refer to the method
    name: Final[str] = "tom-author-field"

    @staticmethod
    def get_usage() -> str:
        # Shown to the API users api/get-watermarking-method. 
        # Update 1: This is done so they know what his method does and that positions and key is not used yet
        # Update 2: Key is implemented now and HMAC
        return "Stores the secret together with an HMAC signature in the PDFs author and subject metadata fields. Position not used yet."

    @staticmethod
    def _sign(secret: str, key: str) -> str:
        # This is a helper function to create a HMAC signature of the secret using the key
        # This is done to make sure that the secret has not been tampered with and that the correct key is used,
        # without the right key you can not calculate the right signature and create a fake watermark
        return hmac.new(key.encode(), secret.encode(), hashlib.sha256).hexdigest()


    def is_watermark_applicable(self, pdf: PdfSource, position: str | None = None) -> bool:
        # It first checks if it can even run on the file. This is called before add_watermark
        # It is for safety reasons
        try:
            data = load_pdf_bytes(pdf)                      # Normalizes input to raw byes
            doc = fitz.open(stream=data, filetype="pdf")    # Try to parse it with PyMuPDF
            # Here i identified that PYMUPDF cannot save a PDF with zero pages when running the pytest,
            # so I created a way to check for that and return if it has no pages in it.
            pdf_has_pages = doc.page_count > 0
            doc.close()                                     # Dont need to have it open so closes it
            return pdf_has_pages

        except Exception:
            return False

    # I have plans to also implement position, 
    def add_watermark(self, pdf: PdfSource, secret: str, key: str, position: str | None = None) -> bytes:
        # This is for capacity and imperceptibility are addressed
        data = load_pdf_bytes(pdf)
        # Check for secret
        if not secret:
            raise ValueError("Secret must be a non-empty string")

        # Also check for key
        if not key:
            raise ValueError("Key must be a non empty string, please input a key.")

        # The value that gets stored.
        stored = secret + "|" + self._sign(secret, key)

        doc = fitz.open(stream=data, filetype="pdf")
        try:
            meta = doc.metadata or {}
            # This is also for capacrity. The author field is just a string with no hard lenght limit
            # this should in theoiry give me some payload capacity, fille name, and ID string. This has not been tested
            # for a maximum capacity yet
            meta["author"] = stored
            meta["subject"] = stored  # small robustness bit: backup copy in case author gets cleared

            # This is for imperceptability
            # the set_metadata only touches the PDFs information dictionary, not the whole page content.
            # This means nothing visible changes when the document is opened and read.
            # I guess this is visible for a normal reading of the document but not to someone who opens the properties, so that
            # would need to be enhanced aswell
            doc.set_metadata(meta)
            out = doc.tobytes()
        finally:
            doc.close()
        return out

    def read_secret(self, pdf: PdfSource, key: str) -> str:
        # This will reverse the add_watermark: open the file and pull the string back out of author field and check the signature with the key
        # Check for key again here
        if not key:
            raise ValueError("Key must be a non empty string, please input a key.")
        
        data = load_pdf_bytes(pdf)
        doc = fitz.open(stream=data, filetype="pdf")
        try:
            meta = doc.metadata or {}
            # Both places the watermark could be stored, author first and subject as backup for now
            stored = meta.get("author") or meta.get("subject") or ""
        finally:
            doc.close()

        # If there is no "|" then the value was not written by this method, so we raise an error. This is for safety and precaution
        if "|" not in stored:
            raise SecretNotFoundError("No secret found in author field or subject field")

        # This splits a group name for example: "group-07|23e2f4 or something like that" secret becomes -> "group-07" and signature becomes -> "23s2f4"
        # Signature only contains numbers from 0-9 and letters a-f 
        secret, signature = stored.rsplit("|", 1)
        
        # Now we calculate the signature again with the key we were given and compare it to the stored one
        # If it is wrong or edided then we raise and error since it did not match
        if not hmac.compare_digest(signature, self._sign(secret, key)):
            raise InvalidKeyError("This is the wrong key or the watermark has been tampered with")

        return secret

# 1. Have written a test with the help of AI in order to test the method i created, got feedback on first few test for: 14 passed, 3 xfailed in 0.15s,
# This allowed me to implement some more fixes like empty pdf aswell as matching key and signature.
# Changed author and subject to be in stored instead of secret, this should make it show up in the authorfiled as intended for "group-xx|signature"
# I believe it is still visible in the properties of the pdf so will have to fix that later on.

# 2. Testing after that provided and after I added HMAC: 7 failed, 9 passed, 1 xfailed in 0.15s. It failed with secretNotFoundError. The add_watermark created stored but
# still saved the plain secret in author/subject, which i probably missed to implement. So it couldnt read back so there was no "|" check and no signature that was read back. Will try to fix by saving stored instead

# 3. After the fix with stored: 14 passed 1 xfailed and 2 failed withing 0.15s. The method should work but I am still getting some XPASS errors on the test. After looking 
# that up is that it expected to fail but they should now pass with the HMAC signature. These tests should pass because of the HMAC signature.
# The last xfail is as i understood when researching and asking AI, is if someone does a complete metadata wipe, I dont really know how to fix that yet. Will have to be something I fix later on.
# What to do until next deadline is to make it more robust by perhaps creating a second copy inside the middle of the page as invisible text or something like that.
# Also implement position to choose where it will be stored.

__all__ = ["AuthorFieldWaterMarking"]