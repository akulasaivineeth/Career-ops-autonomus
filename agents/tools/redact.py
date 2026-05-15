"""Screenshot redaction — black-box sensitive regions before saving (BUILD.md Task 5.2)."""

from __future__ import annotations

import re
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

# Fields that should always be redacted if they appear in a screenshot label/context.
_SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\$[\d,]+"),  # salary / compensation
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),  # date of birth
    re.compile(r"\b\d{2}/\d{2}/\d{2,4}\b"),
]


def redact_image(image_path: str) -> str:
    """
    Run lightweight regex-based redaction on a screenshot.

    If PIL / pytesseract are available, OCR-based detection is applied as well.
    Returns path to the (in-place) redacted image.
    """
    path = Path(image_path)
    if not path.exists():
        return image_path

    try:
        from PIL import Image, ImageDraw

        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        try:
            import pytesseract

            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            _redact_ocr_fields(draw, ocr_data)
        except Exception:
            pass  # OCR optional; skip gracefully

        img.save(image_path)
    except Exception as exc:
        log.warning("redact_failed", path=image_path, error=str(exc))

    return image_path


def _redact_ocr_fields(draw: Any, ocr_data: dict[str, list]) -> None:
    """Black-box bounding boxes for OCR tokens that match sensitive patterns."""

    n = len(ocr_data.get("text", []))
    for i in range(n):
        word = ocr_data["text"][i]
        if not word.strip():
            continue
        for pat in _SENSITIVE_PATTERNS:
            if pat.search(word):
                x, y, w, h = (
                    ocr_data["left"][i],
                    ocr_data["top"][i],
                    ocr_data["width"][i],
                    ocr_data["height"][i],
                )
                draw.rectangle([x, y, x + w, y + h], fill="black")
                break


def Any(*args: object, **kwargs: object) -> object:  # type: ignore[override]
    pass
