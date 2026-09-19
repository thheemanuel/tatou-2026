"""watermarking_method_gustav.py

Individual watermarking method for the Tatou platform (SOFTSEC VT2026).

PDF structure

A PDF is not a single blob: it is a set of numbered *objects*
(dictionaries, arrays, and streams), a cross-reference (xref) table
mapping "object N -> byte offset", and a trailer naming the root
object (/Root) and where the xref starts (startxref). Readers jump
straight to any object via the xref instead of scanning the whole
file. "Incrementally updated" PDFs (re-saved by Acrobat/LibreOffice/
etc.) stack additional xref sections and %%EOF markers on top of the
original rather than rewriting the file from scratch.

Tools for pdf analysis

explore_pdf() in watermarking_utils.py - JSON object
tree with a per-object sha1; already used to inspect a sample file.
`qpdf --qdf --object-streams=disable in.pdf out.pdf` - rewrites a
PDF into a fully human-readable form. https://qpdf.readthedocs.io/
Didier Stevens (the goat???)' pdf-parser.py and blog - practical PDF structure and
malicious-PDF analysis: https://blog.didierstevens.com/programs/pdf-tools/

More
ISO 32000-1:2008 (PDF 1.7) / ISO 32000-2:2020 (PDF 2.0) - the
canonical file-format specification
https://pdfa.org/resource/iso-32000-2/
Kitsos, Papanikolaou et al., "Watermarking PDF Documents using
Various Representations of Self-inverting Permutations" - structural
watermarking (encoding the signal in object order/xref layout rather
than visible content): https://arxiv.org/pdf/1501.02686
Singh & Kasana, "A review of digital watermarking techniques:
Current trends, challenges and opportunities" (2024) - general
robust / fragile / semi-fragile taxonomy:
https://journals.sagepub.com/doi/full/10.3233/WEB-230280
PyMuPDF (fitz) docs, used by explore_pdf() and watermarking_cli.py:
https://pymupdf.readthedocs.io/

--------------------------------------------------------------------
TODO: hide secret as invisible text on page 1 (PDF text-render
# mode 3 = drawn but not painted, like OCR). Read back by extracting page text
# extraction reads the content stream, so invisible text comes back too.
--------------------------------------------------------------------
"""
