# Individual watermarking method for Theodor Gyllner
# Work in progress


# this watermarking method will use two different watermarks, one visible and one invisible.


# the invisible watermark: ******

# saving the secret inside the pdf metadata
# (and for confirmation purposes it will be hashed etc...)

# pdfs contain a lot of metadata such as author, subject or keywords
# in this watermarking method we will save the secret in the "keywords" field!!!


# the visible watermark: *******

# the goal is to produce, by the use of the provided pdf watermarking library, a visible diagonal text on all of the pdf pages.

# the text will be something like "watermarked by group 21"

#*******


# the whole idea is that we use a combination of both these methods.

# idea for future improvement: use stegnography (or whatever it is called) to embed a secret into the image on the pdf. (assuming they have a image... idk).




# to do this (above ^^^^) we need to make some imports


# postpone evaluation of type annotations.
# this is useful for type hints that refer to types that may not yet
# have been evaluated when the function or class is defined.

from __future__ import annotations


# this one is maybe not so important but neverthenless allows me to declare variables I know will never change such as the name of the watermarking method.

# final is a type hint used to indicate that a value is intended
# not to be reassigned. this can be checked by static type checkers,
# but python does not enforce it at runtime.

from typing import Final


# we use hmac-sha256 to authenticate the stored secret.
# sha-256 is the hash function used inside hmac, while hmac also
# incorporates a secret key.
#
# this allows read_secret() to detect an incorrect key or a modified
# secret/authentication tag.

import hashlib
import hmac

import hashlib
import hmac 


# use the import used in the watermark_method.py file that was provided at the beginning.
# it is a python module provided by PyMuPDF and it lets us:
# open pdfs, read metadata, modify metadata, add text to pdf pages and save pdfs

import fitz

# the two properties modify metadata and add text to pdf pages will be relevant for our watermarking !!!


# since it is useful we will also use stuff provided by tatou

from watermarking_method import (InvalidKeyError, PdfSource, SecretNotFoundError, WatermarkingMethod, load_pdf_bytes)






# making sure we use the watermarking method interface
class watermarking_method_theo(WatermarkingMethod):
    
    #declare final variables such as name and other stuff, just like it is done in add_after_eof etc.
    
    name: Final[str] = "theo_group21"
    
    # the name is used when other groups use the api and asks it to use this method.
    
    # just like add_after_eof used constants, we are also going to use them.
    
    
    
    
    
    # i am imagining a string in the metadata that begins with "GROUP21 ..."
    
    _MARKER: Final[str] = "GROUP21:"
    
    # for the diagonal watermarking text
    _VISIBLE_TEXT: Final[str] = "WATERMARKED BY GROUP 21"
    
    
    @staticmethod
    def get_usage() -> str:
        
        return (
        """
        Adds a visible GROUP 21 watermark to every page and stores the secret with an HMAC in pfd metadata, position is currently ignored.
        
        """
            
        )
        
    # unlike the add_after_eof.py watermarking method, we also want to verify
    # the integrity/authenticity of the stored secret using an HMAC.
    # the secret itself is NOT encrypted or hidden by this operation.
    
    @staticmethod
    def sign(secret: str, key: str):
        
        
        # creating a cryptographic signature for the secret
        # using both the secret and the key
        
        # since these kind of methods and operations work on bytes, we will need to convert the secret and key into bytes, from strings
        
        key_b = key.encode("utf-8")
        secret_b = secret.encode("utf-8")
        
        
        # now we calculate the hmac !
        
        signature = hmac.new(key_b, secret_b, hashlib.sha256)
        
        hex_sign = signature.hexdigest()
        
        return hex_sign
    
    # in order to make the visible watermark unique we create this helper function:
    
    @staticmethod
    def make_visible_id(secret: str):
        # create a short unique identifier
        
        digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        
        return digest[:8].upper()
    
    
    # the add_after_eof method includes a method called "is_watermark_applicable"
    # but it checks nothing and only returns True
    
    # therefore in our is_watermark_applicable we will need to implement additional logic in order to determine if the watermark can be applied to the uploaded pdf
    
    # for example, in order to apply the visible watermark, the pdf needs to have pages !!!
    
    
    def is_watermark_applicable(self, pdf: PdfSource, position: str | None = None) -> bool:

        
        # in order to catch exceptions we will need to implement the logic within try-catch blocks
        
        #we will try two scenarios, one where it does not have any pages, and one where the PyMuPDF couldnt open the data as a pdf.
        
        
        
        try:
            
            data = load_pdf_bytes(pdf)
            
            doc = fitz.open(stream=data,filetype="pdf")
            
            try:
                
                #check if it at least contains one page
                
                return doc.page_count > 0
            
            finally:
                
                doc.close()
                
        except Exception:
            
            #if it cannot be opened as a pdf, return false, the watermark cannot be applied.
            return False




# now is time for the actual application of the watermark, which will happen in some steps.

# we need to begin with basic case handling

# maybe a secret or a key isnt provided, we need to raise or catch that kind of scenario.


# then we will add the invisible text to the pdf metadata

# then we will add the visible text to every page in the provided pdf.


# then we return the watermarked pdf (as bytes??? per other methods)

# i wonder why the position is always ignored, it is stated that it is because of api compatibility but i will need to look into that later.

# i want to understand what it is and why it is included at all if it is only ignored later on in methods. (dont have time right now :))

    def add_watermark(self, pdf: PdfSource, secret: str, key: str, position: str | None = None) -> bytes:
    
        if not secret:
            raise ValueError("Secret must not be empty")
    
        if not key:
            raise ValueError("Kay must be not empty")
    
    
    # as per previous methods, convert pdf into bytes and open with fitz
    
        data = load_pdf_bytes(pdf)
    
        doc = fitz.open(stream=data, filetype="pdf")
    
    
    # in order to avoid annoying errors we encapsulate the entire thing in a try -> finally block in order to close the pdf after the whole thing tries running...
    
    
        try:
        
        #part 1, create the invisible watermark
            signature = self.sign(secret, key)
        
            stored_watermark = (self._MARKER + secret + "---" + signature)
            
        # create a short visible identifier derived from the secret
        
            visible_id = self.make_visible_id(secret)
            visible_text = f"{self._VISIBLE_TEXT} - ID: {visible_id}"
        
        # we need to get to the metadata, we need to retrieve it from the pdf
        
            metadata = doc.metadata
        
            metadata["keywords"] = stored_watermark
        
        #update the document with our modified metadata
        
            doc.set_metadata(metadata)
        
        #part 2, create the visible watermark
        
        #loop through the pages in the pdf
        
            for page in doc:
            
            # rect is a class used to define and manipulate four-sided rectangular regions on a pdf page. 
            # with this we can add text to the pdf page and "watermark it"
            
                rect = page.rect
            
            #it works by creating a rectangle on the pdf and then entering the text within that box
            
                watermark_rect = fitz.Rect(
                
                #left side
                    rect.x0,
                #slightly above middle
                    rect.height / 2 - 50,
                #right side of the page
                    rect.x1,
                #slightly below the middle
                    rect.height / 2 + 50,
                )
            
            # write the text
            
                page.insert_textbox(watermark_rect, visible_text, fontsize=30, fontname="helv", align=fitz.TEXT_ALIGN_CENTER, color=(0.7, 0.7, 0.7), overlay=True)
            
            
            #save the watermarking without modifying the id
            
            return doc.tobytes(no_new_id=True)
        
        finally:
        
            doc.close()
            
            
            
    # this read_secret method will need to be reworked, this is a first implementation
    
    def read_secret(self, pdf: PdfSource, key: str) -> str:
        
        # make sure a key was actually supplied by the user
        
        # if not raise an error
        
        if not key:
            raise ValueError("Key must not be empty")
        
        
        # just as done in the previous methods, we need to load the pdf bytes and then open the pdf using PyMuPDF
        
        data = load_pdf_bytes(pdf)
        
        doc =fitz.open(stream=data, filetype="pdf")
        
        #in order to catch exceptions and errors, and that we always need to close the pdf after we have used it, we encapusate in a try-catch or in this case, a try-finally block.
        
        try:
            
            # get metadata such as:
            # title, author, subject, keywords
            metadata = doc.metadata
            
            # the watermarking method i created puts the secret and the "watermark" in the "keywords" field
            stored_watermark = metadata.get("keywords", "") # added empty "" to avoid crash if pdf does not have "keywords" field
            
        finally:
            # we have extracted what we need, so the pdf can now be closed to avoid future wierd errors.
            doc.close()
            
        # now we need to make sure that the extracted watermark was actually ours.
        # if the watermark does not begin with the marker that we used, it isnt our watermarking method being used
        if not stored_watermark.startswith(self._MARKER):
            
            raise SecretNotFoundError("no group 21 watermark was found")
        
        # after confirming that the watermark was ours, we can remove the marker in order to work only with the secret and signature that is the watermark.
        
        # for example, my watermarking method is stored like this "GROUP21:Group07---abcdef123456"
        
        #after the line below, it will be "Group07---abcdef123456"
        
        payload = stored_watermark[len(self._MARKER):]
        
        
        # error handling, if the separation doesnt exist, it wasnt my watermarking method or something else happened.
        if "---" not in payload:
            raise SecretNotFoundError("invalid Group 21 watermark format")
        
        
        #separate the secret (groupXX) from the signature "abcdef123456"
        secret, stored_signature = payload.rsplit("---", 1)
        
        
        # take the extracted values from the keywords field and calculate the same hmac operation that was used when creating the watermark
        expected_signature = self.sign(secret, key)
        
        
        #if not the same, it is incorrect and something has manipulated the watermark or something else has happened, or it isnt our watermarking method.
        if not hmac.compare_digest(stored_signature, expected_signature):
            
            raise InvalidKeyError("incorrect key for group 21 watermark")
        
        #after confirming everything above, it is confirmed that this is our watermarking method and that this is our secret, we can return the secret.
        return secret


