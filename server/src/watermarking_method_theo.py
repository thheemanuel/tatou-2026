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


# allows python type hinting features (declaring that a variable will be a specific type e.g. list[str])
from __future__ import annotations


# this one is maybe not so important but neverthenless allows me to declare variables I know will never change such as the name of the watermarking method.

from typing import Final


# since we will need to verify the secret and stuff like that we need to hash it !! (or use mac, same thing??)
# so import a standard cryptographic hash function

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
        
    # unlike the add_after_eof.py watermarking method we need to encrypt/hash our secret! 
    # so we will need a method for doing just that:
    
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
            
                page.insert_textbox(watermark_rect, self._VISIBLE_TEXT, fontsize=30, fontname="helv", align=fitz.TEXT_ALIGN_CENTER, color=(0.7, 0.7, 0.7), overlay=True)
            
            
            #save the watermarking without modifying the id
            
            return doc.tobytes(no_new_id=True)
        
        finally:
        
            doc.close()
            
            
            
    # this read_secret method will need to be reworked, this is a first implementation
    
    def read_secret(self, pdf: PdfSource, key: str) -> str:
        
        if not key:
            raise ValueError("Key must not be empty")
        
        data = load_pdf_bytes(pdf)
        
        doc =fitz.open(stream=data, filetype="pdf")
        
        try:
            
            metadata = doc.metadata
            
            stored_watermark = metadata.get("keywords", "") # added empty "" to avoid crash if pdf does not have "keywords" field
            
        finally:
            
            doc.close()
            
        
        if not stored_watermark.startswith(self._MARKER):
            
            raise SecretNotFoundError("no group 21 watermark was found")
        
        payload = stored_watermark[len(self._MARKER):]
        
        if "---" not in payload:
            raise SecretNotFoundError("invalid Group 21 watermark format")
        
        secret, stored_signature = payload.rsplit("---", 1)
        
        expected_signature = self.sign(secret, key)
        
        if not hmac.compare_digest(stored_signature, expected_signature):
            
            raise InvalidKeyError("incorrect key for group 21 watermark")
        
        
        return secret


