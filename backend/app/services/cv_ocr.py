from pathlib import Path
from typing import Protocol

from app.core.errors import ApiError


class OCRExtractor(Protocol):
    def extract(self, path: Path) -> str: ...


class OptionalOCRExtractor:
    """Integration point for an OCR engine; manual review remains available."""

    def extract(self, path: Path) -> str:
        raise ApiError(
            422,
            "OCR_FAILED",
            "Aucun moteur OCR local n’est configuré. Continuez avec la saisie manuelle.",
        )
