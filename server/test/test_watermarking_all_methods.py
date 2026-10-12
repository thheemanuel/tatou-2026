# tests/test_watermarking_all_methods.py
from __future__ import annotations
import importlib
import inspect
from pathlib import Path

import fitz
import pytest

from watermarking_method import InvalidKeyError, SecretNotFoundError


# --------- collect all methods from the registry ----------
try:
    wm = importlib.import_module("watermarking_utils")
    METHODS = getattr(wm, "METHODS", {})
except Exception:  # registry/module missing
    METHODS = {}

CASES: list[tuple[str, object]] = [(str(name), impl) for name, impl in (METHODS or {}).items()]

if not CASES:
    pytest.skip("No watermarking methods registered in watermarking_utils.METHODS", allow_module_level=True)


PAGE_TEXT = "Hello Tatou, confidential report."


# --------- fixtures ----------
# The old fixture was a PDF with zero pages, so every method that needs a page
# said "not applicable" and the tests just skipped (found with mutation testing).
# Using a real one-page PDF so the methods actually get tested.
@pytest.fixture(scope="session")
def sample_pdf_path(tmp_path_factory) -> Path:
    """A one-page PDF with some visible text."""
    pdf = tmp_path_factory.mktemp("pdfs") / "sample.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), PAGE_TEXT)
    doc.save(pdf)
    doc.close()
    return pdf

@pytest.fixture(scope="session")
def two_page_pdf_bytes() -> bytes:
    """Two pages and a document title, to check page choice and metadata."""
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), PAGE_TEXT)
    doc.new_page().insert_text((72, 72), "Page two.")
    doc.set_metadata({"title": "Annual report"})
    data = doc.tobytes()
    doc.close()
    return data

@pytest.fixture(scope="session")
def zero_page_pdf_bytes() -> bytes:
    """Has a PDF header but no pages."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"%%EOF\n"
    )

@pytest.fixture(scope="session")
def secret() -> str:
    return "unit-test-secret"

@pytest.fixture(scope="session")
def key() -> str:
    return "unit-test-key"


def _as_instance(impl: object) -> object:
    """Return an instance for class objects; pass instances through."""
    if inspect.isclass(impl):
        return impl()  # assumes zero-arg constructor
    return impl


# --------- parameterization over all methods ----------
@pytest.mark.parametrize("method_name,impl", CASES, ids=[n for n, _ in CASES])
class TestAllWatermarkingMethods:
    def test_is_watermark_applicable(self, method_name: str, impl: object, sample_pdf_path: Path):
        wm_impl = _as_instance(impl)
        ok = wm_impl.is_watermark_applicable(sample_pdf_path, position=None)
        assert ok is True, f"{method_name}: must be applicable to a normal one-page PDF"

    def test_not_applicable_to_non_pdf(self, method_name: str, impl: object):
        wm_impl = _as_instance(impl)
        assert wm_impl.is_watermark_applicable(b"this is not a pdf", position=None) is False

    # create-watermark trusts is_watermark_applicable, so if a method says yes
    # it should also work. Testing the zero pages case.
    def test_applicable_implies_roundtrip_on_zero_pages(self, method_name: str, impl: object, zero_page_pdf_bytes: bytes, key: str):
        wm_impl = _as_instance(impl)
        if wm_impl.is_watermark_applicable(zero_page_pdf_bytes, position=None):
            out = wm_impl.add_watermark(zero_page_pdf_bytes, secret="s", key=key, position=None)
            assert wm_impl.read_secret(out, key=key) == "s"

    def test_roundtrip_on_multi_page_pdf_keeps_metadata(self, method_name: str, impl: object, two_page_pdf_bytes: bytes, key: str):
        wm_impl = _as_instance(impl)
        out = wm_impl.add_watermark(two_page_pdf_bytes, secret="s", key=key, position=None)
        assert wm_impl.read_secret(out, key=key) == "s"
        doc = fitz.open(stream=out, filetype="pdf")
        try:
            assert doc.page_count == 2
            assert doc.metadata["title"] == "Annual report"
        finally:
            doc.close()

    def test_add_watermark_and_shape(self, method_name: str, impl: object, sample_pdf_path: Path, secret: str, key: str):
        wm_impl = _as_instance(impl)
        original = sample_pdf_path.read_bytes()
        out_bytes = wm_impl.add_watermark(sample_pdf_path, secret=secret, key=key, position=None)
        assert isinstance(out_bytes, (bytes, bytearray)), f"{method_name}: add_watermark must return bytes"
        assert len(out_bytes) >= len(original), f"{method_name}: watermarked bytes should not be smaller than input"
        assert out_bytes.startswith(b"%PDF-"), f"{method_name}: output should still look like a PDF"

    def test_watermarked_pdf_stays_usable(self, method_name: str, impl: object, sample_pdf_path: Path, secret: str, key: str):
        wm_impl = _as_instance(impl)
        out_bytes = wm_impl.add_watermark(sample_pdf_path, secret=secret, key=key, position=None)
        doc = fitz.open(stream=out_bytes, filetype="pdf")
        try:
            assert doc.page_count == 1
            assert PAGE_TEXT in doc.load_page(0).get_text()
        finally:
            doc.close()

    def test_read_secret_roundtrip(self, method_name: str, impl: object, sample_pdf_path: Path, secret: str, key: str, tmp_path: Path):
        wm_impl = _as_instance(impl)
        out_pdf = tmp_path / f"{method_name}_watermarked.pdf"
        out_pdf.write_bytes(wm_impl.add_watermark(sample_pdf_path, secret=secret, key=key, position=None))
        extracted = wm_impl.read_secret(out_pdf, key=key)
        assert isinstance(extracted, str), f"{method_name}: read_secret must return str"
        assert extracted == secret, f"{method_name}: read_secret should return the exact embedded secret"

    # The secret can be any text the user types, so test some tricky ones:
    # separators the methods use ("|", "---"), non-Latin text and a long one.
    @pytest.mark.parametrize("tricky_secret", [
        "Gruppe-Österåker",
        "组-07",
        "team 🚀",
        "a|b|c",
        "a---b",
        "line1\nline2",
        "x" * 3000,
    ], ids=["latin1", "cjk", "emoji", "pipes", "dashes", "newline", "long"])
    def test_read_secret_roundtrip_tricky_secrets(self, method_name: str, impl: object, sample_pdf_path: Path, key: str, tricky_secret: str):
        wm_impl = _as_instance(impl)
        out_bytes = wm_impl.add_watermark(sample_pdf_path, secret=tricky_secret, key=key, position=None)
        assert wm_impl.read_secret(out_bytes, key=key) == tricky_secret

    def test_read_secret_wrong_key(self, method_name: str, impl: object, sample_pdf_path: Path, secret: str, key: str):
        wm_impl = _as_instance(impl)
        out_bytes = wm_impl.add_watermark(sample_pdf_path, secret=secret, key=key, position=None)
        with pytest.raises(InvalidKeyError):
            wm_impl.read_secret(out_bytes, key=key + "-wrong")

    def test_read_secret_unwatermarked(self, method_name: str, impl: object, sample_pdf_path: Path, key: str):
        wm_impl = _as_instance(impl)
        with pytest.raises(SecretNotFoundError):
            wm_impl.read_secret(sample_pdf_path, key=key)

    def test_rewatermark_reads_latest(self, method_name: str, impl: object, sample_pdf_path: Path, key: str):
        wm_impl = _as_instance(impl)
        first = wm_impl.add_watermark(sample_pdf_path, secret="first", key=key, position=None)
        second = wm_impl.add_watermark(first, secret="second", key=key, position=None)
        assert wm_impl.read_secret(second, key=key) == "second"

    @pytest.mark.parametrize("bad_secret,bad_key", [("", "k"), ("s", "")], ids=["empty-secret", "empty-key"])
    def test_add_watermark_rejects_empty_inputs(self, method_name: str, impl: object, sample_pdf_path: Path, bad_secret: str, bad_key: str):
        wm_impl = _as_instance(impl)
        with pytest.raises(ValueError):
            wm_impl.add_watermark(sample_pdf_path, secret=bad_secret, key=bad_key, position=None)

    def test_read_secret_rejects_empty_key(self, method_name: str, impl: object, sample_pdf_path: Path, secret: str, key: str):
        wm_impl = _as_instance(impl)
        out_bytes = wm_impl.add_watermark(sample_pdf_path, secret=secret, key=key, position=None)
        with pytest.raises(ValueError):
            wm_impl.read_secret(out_bytes, key="")
