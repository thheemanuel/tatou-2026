"""watermarking_method_gustav.py

Individual watermarking method for the Tatou platform (SOFTSEC VT2026).

--------------------------------------------------------------------
PDF structure, in one paragraph
--------------------------------------------------------------------
A PDF is not a single blob: it is a set of numbered *objects*
(dictionaries, arrays, and streams), a cross-reference (xref) table
mapping "object N -> byte offset", and a trailer naming the root
object (/Root) and where the xref starts (startxref). Readers jump
straight to any object via the xref instead of scanning the whole
file. "Incrementally updated" PDFs (re-saved by Acrobat/LibreOffice/
etc.) stack additional xref sections and %%EOF markers on top of the
original rather than rewriting the file from scratch.

--------------------------------------------------------------------
Where a watermark can live (design space, roughly weakest -> hardest
to strip; strength trades off against implementation effort and
against how "normal" the technique looks in a raw object dump)
--------------------------------------------------------------------
1. Trailing / incremental-update bytes  (e.g. the built-in `toy-eof`)
   - Append data after the final %%EOF.
   - Weakest: destroyed by any re-save/flatten of the file.

2. Metadata (/Info dict, XMP stream)
   - Easy to add, but exactly where "clean metadata" tools look first.

3. Extra/unused key on an existing object
   - e.g. an extra key on a page's resource dictionary.
   - Not metadata-shaped, but trivially found by dumping objects
     (see Tools below) - anyone who looks, finds it.

4. Content-stream level
   - Encode bits in the page's actual drawing instructions: invisible
     text, whitespace/operator-order variation, micro glyph shifts.
   - Requires understanding PDF content-stream operators to find and
     remove; survives naive "strip metadata" tooling.

5. Structural / object-graph level
   - Object ordering, generation numbers, xref layout choices carry
     the signal instead of (or alongside) visible content.
   - Hardest to strip without fully rebuilding the file from rendered
     output. See Kitsos et al. (self-inverting permutations) below for
     a worked academic example of this category.

6. Image steganography (conditional - only if the PDF has images)
   - LSB-encode bits into embedded raster pixel data before it is
     compressed into the image stream.
   - Caveat: PDF images are often JPEG/DCT (lossy) - recompressing the
     image destroys LSB-level changes. Gate this with
     is_watermark_applicable() rather than assuming every PDF has a
     usable image.

Per the course's own RMAP spec, methods may be combined ("your single
best watermarking technique, or a combination of several methods
applied together") for defense in depth - an attacker then has to
find and strip every layer, not just the first one they notice.

--------------------------------------------------------------------
Tools used to actually look inside a PDF while designing this
--------------------------------------------------------------------
- explore_pdf() in watermarking_utils.py (this repo) - JSON object
  tree with a per-object sha1; already used to inspect a sample file.
- `qpdf --qdf --object-streams=disable in.pdf out.pdf` - rewrites a
  PDF into a fully human-readable form. https://qpdf.readthedocs.io/
- Didier Stevens' pdf-parser.py and blog - practical PDF structure and
  malicious-PDF analysis: https://blog.didierstevens.com/programs/pdf-tools/

--------------------------------------------------------------------
Sources / further reading
--------------------------------------------------------------------
- ISO 32000-1:2008 (PDF 1.7) / ISO 32000-2:2020 (PDF 2.0) - the
  canonical file-format specification, freely downloadable via the
  PDF Association: https://pdfa.org/resource/iso-32000-2/
- Didier Stevens, PDF internals & malicious-PDF analysis:
  https://blog.didierstevens.com/programs/pdf-tools/
- Kitsos, Papanikolaou et al., "Watermarking PDF Documents using
  Various Representations of Self-inverting Permutations" - structural
  watermarking, category 5 above: https://arxiv.org/pdf/1501.02686
- Singh & Kasana, "A review of digital watermarking techniques:
  Current trends, challenges and opportunities" (2024) - general
  robust / fragile / semi-fragile taxonomy:
  https://journals.sagepub.com/doi/full/10.3233/WEB-230280
- PyMuPDF (fitz) docs, used by explore_pdf() and watermarking_cli.py:
  https://pymupdf.readthedocs.io/

--------------------------------------------------------------------
TODO(gustav): pick one approach from the design space above and write
the concrete reasoning here before implementing - what makes it
survive stripping, what its known weak point is, and why that
trade-off was chosen over the alternatives. This is the part the oral
exam will actually ask about.
--------------------------------------------------------------------
"""
