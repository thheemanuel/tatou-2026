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
"""

from __future__ import annotations

from typing import Final

import fitz  # PyMuPDF

from watermarking_method import (
    PdfSource,
    SecretNotFoundError,
    WatermarkingMethod,
    load_pdf_bytes,
)


class InvisibleTextWatermark(WatermarkingMethod):
    """Hides the secret as invisible text on the first page."""

    # Registry key other modules look this method up by.
    name: Final[str] = "invisible-text"

    # Tag prepended to the hidden text so we can find our payload later.
    _MARKER: Final[str] = "TATOUWM:"

    @staticmethod
    def get_usage() -> str:
        # Pure documentation string surfaced by the CLI; no logic here.
        return "Embeds the secret as invisible text on the first page. Position is ignored."

    def is_watermark_applicable(
        self,
        pdf: PdfSource,
        position: str | None = None,
    ) -> bool:
        try:
            # Normalize input to bytes, then let PyMuPDF parse it.
            doc = fitz.open(stream=load_pdf_bytes(pdf), filetype="pdf")
            ok = doc.page_count > 0
            doc.close()
            return ok
        except Exception:
            # Contract says this returns bool, never raises: any failure
            # (corrupt file, etc.) just means "not applicable".
            return False

    def add_watermark(
        self,
        pdf: PdfSource,
        secret: str,
        key: str,
        position: str | None = None,
    ) -> bytes:
        doc = fitz.open(stream=load_pdf_bytes(pdf), filetype="pdf")
        page = doc.load_page(0)
        # The actual watermark: a text-show operation with the PDF `Tr`
        # (text rendering mode) operator set to 3 = invisible. The glyphs
        # are recorded in the content stream but never painted.
        page.insert_text((0, 10), self._MARKER + secret, fontsize=1, render_mode=3)
        # no_new_id=True stops PyMuPDF from randomizing the trailer /ID
        # on save, which would otherwise break determinism.
        out = doc.tobytes(no_new_id=True)
        doc.close()
        return out

    def read_secret(self, pdf: PdfSource, key: str) -> str:
        doc = fitz.open(stream=load_pdf_bytes(pdf), filetype="pdf")
        # get_text() returns invisible-mode glyphs too, since it reads the
        # content stream rather than rendering pixels.
        text = doc.load_page(0).get_text()
        doc.close()

        idx = text.find(self._MARKER)
        if idx == -1:
            raise SecretNotFoundError("No watermark found")
        # Everything after the marker is the secret we embedded.
        return text[idx + len(self._MARKER):].strip()


__all__ = ["InvisibleTextWatermark"]

