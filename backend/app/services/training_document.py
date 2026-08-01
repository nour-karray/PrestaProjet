from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.documents.renderers import render_document
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.models.training_document import DocumentStatus, DocumentType, TrainingDocument
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.repositories.training_document import TrainingDocumentRepository
from app.repositories.training_pricing import TrainingPricingRepository
from app.repositories.training_program import TrainingProgramRepository
from app.schemas.training_document import (
    DocumentGenerationResult,
    GenerateAllResponse,
    TrainingDocumentResponse,
)
from app.services.training_pricing import TrainingPricingService
from app.storage.documents import DocumentStorage

DOCUMENT_NAMES = {
    DocumentType.PROGRAM: "Programme PDF",
    DocumentType.QUOTE: "Devis",
    DocumentType.AGREEMENT: "Convention",
    DocumentType.ATTENDANCE_SHEET: "Feuille de présence",
    DocumentType.CERTIFICATE: "Attestation",
}
FILE_PREFIXES = {
    DocumentType.PROGRAM: "programme",
    DocumentType.QUOTE: "devis",
    DocumentType.AGREEMENT: "convention",
    DocumentType.ATTENDANCE_SHEET: "feuille_presence",
    DocumentType.CERTIFICATE: "attestation",
}


class TrainingDocumentService:
    def __init__(self, session: Session, storage: DocumentStorage | None = None) -> None:
        self.session = session
        self.cases = TrainingCaseRepository(session)
        self.documents = TrainingDocumentRepository(session)
        self.programs = TrainingProgramRepository(session)
        self.pricings = TrainingPricingRepository(session)
        self.activities = ActivityRepository(session)
        self.storage = storage or DocumentStorage()

    def list_documents(self, case_id: UUID) -> list[TrainingDocumentResponse]:
        training_case = self._get_case(case_id)
        if training_case.status == TrainingCaseStatus.TARIFICATION_VALIDEE.value:
            return []
        return [
            TrainingDocumentResponse.model_validate(item)
            for item in self.documents.list_by_case(case_id)
        ]

    def initialize(self, case_id: UUID, administrator_id: UUID) -> list[TrainingDocumentResponse]:
        training_case = self._get_case_for_change(case_id)
        allowed = {
            TrainingCaseStatus.TARIFICATION_VALIDEE.value,
            TrainingCaseStatus.DOCUMENTS_A_GENERER.value,
            TrainingCaseStatus.DOCUMENTS_GENERES.value,
        }
        if training_case.status not in allowed:
            self._invalid_status()
        self._ensure_dependencies(training_case)
        existing = {item.document_type for item in self.documents.list_by_case(case_id)}
        for document_type, name in DOCUMENT_NAMES.items():
            if document_type.value not in existing:
                self.documents.add(
                    TrainingDocument(
                        training_case_id=case_id,
                        document_type=document_type.value,
                        status=DocumentStatus.PENDING.value,
                        display_name=name,
                    )
                )
        if training_case.status == TrainingCaseStatus.TARIFICATION_VALIDEE.value:
            training_case.status = TrainingCaseStatus.DOCUMENTS_A_GENERER.value
            self._log(administrator_id, training_case, "DocumentsInitialized", {"count": 5})
        self.session.commit()
        return self.list_documents(case_id)

    def generate(
        self, case_id: UUID, document_type: DocumentType, administrator_id: UUID
    ) -> TrainingDocumentResponse:
        training_case = self._get_case_for_change(case_id)
        if training_case.status == TrainingCaseStatus.TARIFICATION_VALIDEE.value:
            self.initialize(case_id, administrator_id)
            training_case = self._get_case_for_change(case_id)
        if training_case.status not in {
            TrainingCaseStatus.DOCUMENTS_A_GENERER.value,
            TrainingCaseStatus.DOCUMENTS_GENERES.value,
        }:
            self._invalid_status()
        self._ensure_dependencies(training_case)
        document = self.documents.get(case_id, document_type, for_update=True)
        if document is None:
            raise ApiError(404, "TRAINING_DOCUMENT_NOT_FOUND", "Le document est introuvable.")
        was_generated = document.status == DocumentStatus.GENERATED.value
        old_path = document.relative_path
        new_path: str | None = None
        try:
            snapshot = self._snapshot(training_case, document_type)
            content = render_document(document_type.value, snapshot)
            stored = self.storage.store(case_id, document_type.value, content)
            new_path = stored.relative_path
            document.status = DocumentStatus.GENERATED.value
            document.internal_filename = stored.internal_filename
            document.original_filename = (
                f"{FILE_PREFIXES[document_type]}_{training_case.reference}.pdf"
            )
            document.relative_path = stored.relative_path
            document.mime_type = "application/pdf"
            document.file_size = stored.file_size
            document.sha256 = stored.sha256
            document.snapshot_data = snapshot
            document.generation_error = None
            document.generated_at = datetime.now(UTC)
            self._refresh_workflow(training_case, administrator_id)
            self._log(
                administrator_id,
                training_case,
                "TrainingDocumentRegenerated" if was_generated else "TrainingDocumentGenerated",
                {"document_type": document_type.value},
            )
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            if new_path:
                self.storage.delete(new_path)
            if was_generated:
                raise ApiError(
                    500, "DOCUMENT_GENERATION_FAILED", "La régénération a échoué."
                ) from exc
            failed = self.documents.get(case_id, document_type, for_update=True)
            if failed:
                failed.status = DocumentStatus.FAILED.value
                failed.generation_error = "La génération du PDF a échoué."
                self._log(
                    administrator_id,
                    training_case,
                    "TrainingDocumentGenerationFailed",
                    {"document_type": document_type.value},
                )
                self.session.commit()
            raise ApiError(
                500, "DOCUMENT_GENERATION_FAILED", "La génération du PDF a échoué."
            ) from exc
        if old_path and old_path != new_path:
            self.storage.delete(old_path)
        return TrainingDocumentResponse.model_validate(document)

    def generate_all(self, case_id: UUID, administrator_id: UUID) -> GenerateAllResponse:
        if not self.documents.list_by_case(case_id):
            self.initialize(case_id, administrator_id)
        results = []
        for document_type in DocumentType:
            current = self.documents.get(case_id, document_type)
            if current and current.status == DocumentStatus.GENERATED.value:
                results.append(
                    DocumentGenerationResult(
                        document_type=document_type,
                        success=True,
                        document=TrainingDocumentResponse.model_validate(current),
                    )
                )
                continue
            try:
                generated = self.generate(case_id, document_type, administrator_id)
                results.append(
                    DocumentGenerationResult(
                        document_type=document_type, success=True, document=generated
                    )
                )
            except ApiError as exc:
                failed = self.documents.get(case_id, document_type)
                if failed is None:
                    raise
                results.append(
                    DocumentGenerationResult(
                        document_type=document_type,
                        success=False,
                        document=TrainingDocumentResponse.model_validate(failed),
                        error=exc.message,
                    )
                )
        all_generated = all(item.success for item in results)
        training_case = self._get_case(case_id)
        self._log(
            administrator_id,
            training_case,
            "TrainingDocumentsBatchCompleted",
            {"success_count": sum(item.success for item in results), "total": 5},
        )
        self.session.commit()
        return GenerateAllResponse(results=results, all_generated=all_generated)

    def download(
        self, case_id: UUID, document_type: DocumentType, administrator_id: UUID
    ) -> tuple[Path, str]:
        training_case = self._get_case(case_id)
        document = self.documents.get(case_id, document_type)
        if (
            document is None
            or document.status != DocumentStatus.GENERATED.value
            or not document.relative_path
        ):
            raise ApiError(404, "TRAINING_DOCUMENT_FILE_NOT_FOUND", "Le PDF est indisponible.")
        path = self.storage.resolve(document.relative_path)
        if not path.is_file():
            raise ApiError(404, "TRAINING_DOCUMENT_FILE_NOT_FOUND", "Le PDF est indisponible.")
        self._log(
            administrator_id,
            training_case,
            "TrainingDocumentDownloaded",
            {"document_type": document_type.value},
        )
        self.session.commit()
        return path, document.original_filename or "document.pdf"

    def _snapshot(self, training_case: TrainingCase, document_type: DocumentType) -> dict:
        program = self.programs.get_by_case(training_case.id)
        pricing = self.pricings.get_by_case(training_case.id)
        need = training_case.training_need
        if need is None or not need.is_validated:
            raise ApiError(409, "TRAINING_NEED_NOT_VALIDATED", "Le besoin doit être validé.")
        if program is None or not program.is_validated:
            raise ApiError(
                409,
                "TRAINING_PROGRAM_NOT_VALIDATED",
                "Le programme doit être validé.",
            )
        if pricing is None or not pricing.is_validated:
            raise ApiError(
                409,
                "TRAINING_PRICING_NOT_VALIDATED",
                "La tarification doit être validée.",
            )
        if training_case.trainer is None:
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté.")
        totals = TrainingPricingService._totals(pricing)
        total_theory = total_practice = 0
        days = []
        for day in program.days:
            modules = []
            for item in sorted(
                (x for x in day.items if x.parent_id is None), key=lambda x: x.position
            ):
                total_theory += item.theory_minutes
                total_practice += item.practice_minutes
                children = []
                for child in sorted(item.children, key=lambda x: x.position):
                    total_theory += child.theory_minutes
                    total_practice += child.practice_minutes
                    children.append(
                        {
                            "title": child.title,
                            "duration": self._duration(
                                child.theory_minutes + child.practice_minutes
                            ),
                        }
                    )
                modules.append(
                    {
                        "position": item.position,
                        "title": item.title,
                        "content": item.content,
                        "duration": self._duration(item.theory_minutes + item.practice_minutes),
                        "submodules": children,
                    }
                )
            days.append({"title": day.title, "modules": modules})
        vat_note = (
            pricing.vat_exemption_reason or pricing.vat_legal_reference
            if pricing.vat_rate == 0
            else None
        )
        return {
            "document_type": document_type.value,
            "display_name": DOCUMENT_NAMES[document_type],
            "generated_on": datetime.now(UTC).strftime("%d/%m/%Y"),
            "case": {
                "reference": training_case.reference,
                "theme": training_case.theme,
                "description": training_case.description,
            },
            "company": {"name": training_case.company.name},
            "contact": {
                "full_name": training_case.primary_contact.full_name
                if training_case.primary_contact
                else "Non renseigné"
            },
            "trainer": {"full_name": training_case.trainer.full_name},
            "need": {
                "location": need.location,
                "participant_count": need.participant_count,
                "period": self._period(need.desired_start_date, need.desired_end_date),
            },
            "program": {
                "title": program.title,
                "objectives": program.general_objectives or need.objectives,
                "prerequisites": program.prerequisites,
                "duration": self._duration(total_theory + total_practice),
                "theory": self._duration(total_theory),
                "practice": self._duration(total_practice),
                "day_count": len(days),
                "days": days,
            },
            "pricing": {
                "currency": "TND",
                "total_excluding_tax": self._money(totals["total_excluding_tax"]),
                "vat_rate": self._rate(pricing.vat_rate),
                "vat_amount": self._money(totals["vat_amount"]),
                "total_including_tax": self._money(totals["total_including_tax"]),
                "vat_note": vat_note,
            },
        }

    def _ensure_dependencies(self, training_case: TrainingCase) -> None:
        program = self.programs.get_by_case(training_case.id)
        pricing = self.pricings.get_by_case(training_case.id)
        if not training_case.training_need or not training_case.training_need.is_validated:
            raise ApiError(409, "TRAINING_NEED_NOT_VALIDATED", "Le besoin doit être validé.")
        if not program or not program.is_validated:
            raise ApiError(409, "TRAINING_PROGRAM_NOT_VALIDATED", "Le programme doit être validé.")
        if not pricing or not pricing.is_validated:
            raise ApiError(
                409, "TRAINING_PRICING_NOT_VALIDATED", "La tarification doit être validée."
            )
        if not training_case.trainer:
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté.")

    def _refresh_workflow(self, training_case: TrainingCase, administrator_id: UUID) -> None:
        documents = self.documents.list_by_case(training_case.id)
        if len(documents) == 5 and all(
            item.status == DocumentStatus.GENERATED.value and item.relative_path
            for item in documents
        ):
            training_case.status = TrainingCaseStatus.DOCUMENTS_GENERES.value
            self._log(administrator_id, training_case, "TrainingDocumentsGenerated", {"count": 5})

    def _get_case(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get(case_id)
        if not training_case:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        return training_case

    def _get_case_for_change(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get_for_update(case_id)
        if not training_case:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        if training_case.is_archived or training_case.status in {
            TrainingCaseStatus.ANNULE.value,
            TrainingCaseStatus.TERMINE.value,
        }:
            self._invalid_status()
        return training_case

    def _log(self, administrator_id, training_case, action, details):
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                training_case_id=training_case.id,
                action=action,
                entity_type="TrainingDocument",
                details=details,
            )
        )

    @staticmethod
    def _invalid_status():
        raise ApiError(
            409, "INVALID_TRAINING_CASE_STATUS", "Le statut du dossier ne permet pas cette action."
        )

    @staticmethod
    def _duration(minutes: int) -> str:
        return f"{minutes // 60} h {minutes % 60:02d}" if minutes % 60 else f"{minutes // 60} h"

    @staticmethod
    def _period(start, end) -> str:
        if not start:
            return "À définir"
        return (
            start.strftime("%d/%m/%Y")
            if not end or end == start
            else f"{start:%d/%m/%Y} au {end:%d/%m/%Y}"
        )

    @staticmethod
    def _money(value: Decimal) -> str:
        return f"{value:,.3f}".replace(",", " ").replace(".", ",") + " TND"

    @staticmethod
    def _rate(value: Decimal) -> str:
        return f"{value:.3f}".replace(".", ",") + " %"
