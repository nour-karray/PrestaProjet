import hashlib
import re
import zipfile
from io import BytesIO
from pathlib import Path, PurePath, PureWindowsPath
from uuid import uuid4

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.config import settings
from app.core.errors import ApiError

ALLOWED_FILES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
SAFE_FILENAME = re.compile(r"^[\w .()'-]+$", re.UNICODE)


class CVStorageService:
    def __init__(self) -> None:
        self.directory = settings.cv_storage_dir
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, extension: str) -> str:
        storage_filename = f"{uuid4()}{extension}"
        self.get_path(storage_filename).write_bytes(content)
        return storage_filename

    def delete(self, storage_filename: str) -> None:
        self.get_path(storage_filename).unlink(missing_ok=True)

    def exists(self, storage_filename: str) -> bool:
        return self.get_path(storage_filename).is_file()

    def get_path(self, storage_filename: str) -> Path:
        if Path(storage_filename).name != storage_filename:
            raise ApiError(422, "INVALID_STORAGE_FILENAME", "Le nom de stockage est invalide.")
        path = (self.directory / storage_filename).resolve()
        if path.parent != self.directory.resolve():
            raise ApiError(422, "INVALID_STORAGE_PATH", "Le chemin de stockage est invalide.")
        return path

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


def validate_cv_file(filename: str | None, mime_type: str, content: bytes) -> str:
    original_filename = filename or ""
    _validate_filename(original_filename)
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_FILES or ALLOWED_FILES[extension] != mime_type:
        raise ApiError(422, "FILE_INVALID", "Le CV doit Ãªtre un PDF ou DOCX valide.")
    if not content:
        raise ApiError(422, "FILE_INVALID", "Le fichier CV est vide.")
    if len(content) > settings.max_cv_file_size_mb * 1024 * 1024:
        raise ApiError(413, "FILE_TOO_LARGE", "Le fichier CV dÃ©passe la taille autorisÃ©e.")
    _validate_signature(content, extension)
    return extension


def _validate_filename(filename: str) -> None:
    if not filename or PurePath(filename).is_absolute() or PureWindowsPath(filename).is_absolute():
        raise ApiError(422, "INVALID_CV_FILENAME", "Le nom du fichier est invalide.")
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ApiError(422, "INVALID_CV_FILENAME", "Le nom du fichier est invalide.")
    if not SAFE_FILENAME.fullmatch(filename):
        raise ApiError(
            422, "INVALID_CV_FILENAME", "Le nom du fichier contient des caractÃ¨res interdits."
        )
    if len(Path(filename).suffixes) != 1:
        raise ApiError(422, "INVALID_CV_FILENAME", "Les doubles extensions sont interdites.")


def _validate_signature(content: bytes, extension: str) -> None:
    try:
        if extension == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise ValueError
            PdfReader(BytesIO(content))
            return
        if not content.startswith(b"PK\x03\x04"):
            raise ValueError
        with zipfile.ZipFile(BytesIO(content)) as archive:
            if "word/document.xml" not in archive.namelist():
                raise ValueError
    except (ValueError, OSError, PdfReadError, zipfile.BadZipFile) as exc:
        raise ApiError(422, "FILE_INVALID", "Le fichier CV est corrompu.") from exc

