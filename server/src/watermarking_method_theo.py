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
        
    
    
    








