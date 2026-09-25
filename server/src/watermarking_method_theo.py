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
    
    
    
    
    # the add_after_eof method includes a method called "is_watermark_applicable"
    # but it checks nothing and only returns True
    
    # therefore in our is_watermark_applicable we will need to implement additional logic in order to determine if the watermark can be applied to the uploaded pdf
    
    # for example, in order to apply the visible watermark, the pdf needs to have pages !!!
    
    
    def is_watermark_applicable(self, pdf: PdfSource, position: str | None = None) -> bool:





        return False


