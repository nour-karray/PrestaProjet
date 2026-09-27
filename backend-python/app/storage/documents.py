import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import settings


@dataclass(frozen=True)
class StoredDocument:
    internal_filename: str
    relative_path: str
    file_size: int
    sha256: str
    absolute_path: Path


class DocumentStorage:
    def __init__(self, root: Path | None = None, max_size_mb: int | None = None) -> None:
        self.root = (root or settings.document_storage_path).resolve()
        self.max_bytes = (max_size_mb or settings.document_max_size_mb) * 1024 * 1024

    def store(self, case_id: UUID, document_type: str, content: bytes) -> StoredDocument:
        if not content.startswith(b"%PDF") or not content.strip():
            raise ValueError("Le fichier généré n’est pas un PDF valide.")
        if len(content) > self.max_bytes:
            raise ValueError("Le PDF généré dépasse la taille maximale autorisée.")
        directory = self._safe_path(str(case_id), document_type.lower())
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4()}.pdf"
        destination = self._safe_path(str(case_id), document_type.lower(), filename)
        handle, temporary_name = tempfile.mkstemp(prefix=".tmp-", suffix=".pdf", dir=directory)
        try:
            with os.fdopen(handle, "wb") as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, destination)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        return StoredDocument(
            internal_filename=filename,
            relative_path=destination.relative_to(self.root).as_posix(),
            file_size=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            absolute_path=destination,
        )

    def resolve(self, relative_path: str) -> Path:
        if ".." in Path(relative_path).parts:
            raise ValueError("Chemin documentaire invalide.")
        path = (self.root / relative_path).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Chemin documentaire invalide.")
        return path

    def delete(self, relative_path: str | None) -> None:
        if relative_path:
            self.resolve(relative_path).unlink(missing_ok=True)

    def _safe_path(self, *parts: str) -> Path:
        path = self.root.joinpath(*parts).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Chemin documentaire invalide.")
        return path
