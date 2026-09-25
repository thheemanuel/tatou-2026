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
