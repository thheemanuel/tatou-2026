# Tests for my invisible-text method. I wrote these after mutation testing
# showed that a lot of mutants in watermarking_method_gustav.py survived.
from __future__ import annotations

import fitz
import pytest

from watermarking_method import InvalidKeyError, SecretNotFoundError
from watermarking_method_gustav import InvisibleTextWatermark

KEY = "unit-test-key"


@pytest.fixture
def pdf_bytes() -> bytes:
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Hello Tatou")
    data = doc.tobytes()
    doc.close()
    return data


def _render(data: bytes) -> bytes:
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        return doc.load_page(0).get_pixmap(dpi=72).samples
    finally:
        doc.close()


def _with_text(data: bytes, text: str, y: float = 20) -> bytes:
    doc = fitz.open(stream=data, filetype="pdf")
    doc.load_page(0).insert_text((0, y), text, fontsize=1, render_mode=3)
    out = doc.tobytes()
    doc.close()
    return out


# The watermark should be invisible, so the page should look exactly the same
# before and after (compares the rendered pixels). This catches mutants that
# change render_mode, font size or position.
def test_watermark_is_invisible(pdf_bytes):
    out = InvisibleTextWatermark().add_watermark(pdf_bytes, secret="group-07", key=KEY)
    assert _render(out) == _render(pdf_bytes)


# Same input should give the exact same bytes every time
# (catches the no_new_id=True -> False mutant).
def test_watermark_is_deterministic(pdf_bytes):
    m = InvisibleTextWatermark()
    assert m.add_watermark(pdf_bytes, "s", KEY) == m.add_watermark(pdf_bytes, "s", KEY)


def test_decoy_marker_does_not_hide_real_watermark(pdf_bytes):
    m = InvisibleTextWatermark()
    marked = m.add_watermark(pdf_bytes, secret="real", key=KEY)
    decoy = _with_text(marked, "TATOUWM2:ZmFrZQ==|deadbeef")
    assert m.read_secret(decoy, key=KEY) == "real"


def test_malformed_decoy_does_not_hide_real_watermark(pdf_bytes):
    m = InvisibleTextWatermark()
    marked = m.add_watermark(pdf_bytes, secret="real", key=KEY)
    for decoy in ("TATOUWM2:no-separator", "TATOUWM2:%%%|bad-base64"):
        assert m.read_secret(_with_text(marked, decoy), key=KEY) == "real"


# If someone adds text to the page later (like a stamp), reading should still work.
def test_text_added_after_watermark(pdf_bytes):
    m = InvisibleTextWatermark()
    marked = m.add_watermark(pdf_bytes, secret="real", key=KEY)
    doc = fitz.open(stream=marked, filetype="pdf")
    doc.load_page(0).insert_text((0, 10.2), " APPROVED BY LEGAL", fontsize=1)
    assert m.read_secret(doc.tobytes(), key=KEY) == "real"


def test_forged_payload_without_key_is_rejected(pdf_bytes):
    forged = _with_text(pdf_bytes, "TATOUWM2:ZmFrZQ==|deadbeef")
    with pytest.raises(InvalidKeyError):
        InvisibleTextWatermark().read_secret(forged, key=KEY)


def test_marker_without_payload_is_not_found(pdf_bytes):
    with pytest.raises(SecretNotFoundError):
        InvisibleTextWatermark().read_secret(_with_text(pdf_bytes, "TATOUWM2:nothing-here"), key=KEY)


def test_legacy_v1_watermark_still_readable(pdf_bytes):
    sig = InvisibleTextWatermark._sign("old-secret", KEY)
    legacy = _with_text(pdf_bytes, "TATOUWM:old-secret|" + sig, y=10)
    assert InvisibleTextWatermark().read_secret(legacy, key=KEY) == "old-secret"


def test_legacy_v1_watermark_with_separator_in_secret(pdf_bytes):
    sig = InvisibleTextWatermark._sign("a|b", KEY)
    legacy = _with_text(pdf_bytes, "TATOUWM:a|b|" + sig, y=10)
    assert InvisibleTextWatermark().read_secret(legacy, key=KEY) == "a|b"


def test_legacy_v1_watermark_wrong_key(pdf_bytes):
    sig = InvisibleTextWatermark._sign("old-secret", KEY)
    legacy = _with_text(pdf_bytes, "TATOUWM:old-secret|" + sig, y=10)
    with pytest.raises(InvalidKeyError):
        InvisibleTextWatermark().read_secret(legacy, key="other")


def test_secret_too_long_is_rejected_not_truncated(pdf_bytes):
    with pytest.raises(ValueError):
        InvisibleTextWatermark().add_watermark(pdf_bytes, secret="x" * 300_000, key=KEY)


def test_signature_is_bound_to_context():
    # The HMAC should be over CONTEXT + secret, not just the secret.
    import hashlib
    import hmac

    plain = hmac.new(KEY.encode(), b"s", hashlib.sha256).hexdigest()
    assert InvisibleTextWatermark._sign("s", KEY) != plain
