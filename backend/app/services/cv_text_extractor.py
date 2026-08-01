import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import ApiError

MIN_USEFUL_CHARACTERS = 40
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass(frozen=True)
class CVTextExtractionResult:
    text: str
    page_count: int | None
    character_count: int
    warnings: list[str] = field(default_factory=list)


class CVTextExtractor:
    def extract(self, path: Path, mime_type: str) -> CVTextExtractionResult:
        if not path.is_file():
            raise ApiError(404, "FILE_INVALID", "Le fichier du CV est introuvable.")
        if mime_type == "application/pdf":
            text, pages = self._extract_pdf(path)
            cleaned = clean_cv_text(text)
            result = CVTextExtractionResult(cleaned, pages, len(cleaned))
        elif mime_type == DOCX_MIME:
            cleaned = clean_cv_text(self._extract_docx(path))
            result = CVTextExtractionResult(cleaned, None, len(cleaned))
        else:
            raise ApiError(422, "FILE_INVALID", "Le format du CV n’est pas pris en charge.")
        if result.character_count < MIN_USEFUL_CHARACTERS:
            raise ApiError(
                422,
                "TEXT_EXTRACTION_EMPTY",
                "Aucun texte exploitable n’a été extrait. "
                "Une OCR ou une saisie manuelle est nécessaire.",
            )
        return result

    @staticmethod
    def _extract_pdf(path: Path) -> tuple[str, int]:
        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                raise ApiError(
                    422, "PDF_ENCRYPTED", "Le fichier PDF est protégé par un mot de passe."
                )
            pages = [page.extract_text() or "" for page in reader.pages]
        except ApiError:
            raise
        except (OSError, PdfReadError) as exc:
            raise ApiError(422, "FILE_INVALID", "Le fichier PDF est corrompu.") from exc
        return "\n\n".join(pages), len(pages)

    @staticmethod
    def _extract_docx(path: Path) -> str:
        try:
            with zipfile.ZipFile(path) as archive:
                root = ElementTree.fromstring(archive.read("word/document.xml"))
        except (OSError, KeyError, ElementTree.ParseError, zipfile.BadZipFile) as exc:
            raise ApiError(422, "FILE_INVALID", "Le fichier DOCX est corrompu.") from exc
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        lines: list[str] = []
        body = root.find(f".//{namespace}body")
        if body is None:
            return ""
        for element in body:
            if element.tag == f"{namespace}p":
                line = "".join(node.text or "" for node in element.iter(f"{namespace}t"))
                if line.strip():
                    lines.append(line)
            elif element.tag == f"{namespace}tbl":
                for row in element.iter(f"{namespace}tr"):
                    cells = [
                        " ".join(node.text or "" for node in cell.iter(f"{namespace}t")).strip()
                        for cell in row.iter(f"{namespace}tc")
                    ]
                    if any(cells):
                        lines.append(" | ".join(cells))
        return "\n".join(lines)


def clean_cv_text(value: str) -> str:
    value = CONTROL_CHARACTERS.sub("", value.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.split("\n")]
    result: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line
        if not (blank and previous_blank):
            result.append(line)
        previous_blank = blank
    return "\n".join(result).strip()
