from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.trainer import Trainer
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.models.training_pricing import (
    TrainerCostInitializationMethod,
    TrainingPricing,
)
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.repositories.training_pricing import TrainingPricingRepository
from app.repositories.training_program import TrainingProgramRepository
from app.schemas.training_pricing import (
    ALLOWED_VAT_RATES,
    TrainingPricingResponse,
    TrainingPricingUpdate,
)

MONEY_QUANTUM = Decimal("0.001")
RATE_QUANTUM = Decimal("0.001")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class TrainingPricingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.cases = TrainingCaseRepository(session)
        self.programs = TrainingProgramRepository(session)
        self.pricings = TrainingPricingRepository(session)
        self.activities = ActivityRepository(session)

    def get(self, case_id: UUID) -> TrainingPricingResponse:
        self._get_case(case_id)
        return self._response(self._get_pricing(case_id))

    def create(self, case_id: UUID, administrator_id: UUID) -> TrainingPricingResponse:
        training_case = self._get_case_for_change(case_id)
        if self.pricings.get_by_case(case_id) is not None:
            raise ApiError(
                409,
                "TRAINING_PRICING_ALREADY_EXISTS",
                "Une tarification existe déjà pour ce dossier.",
            )
        if training_case.status != TrainingCaseStatus.PROGRAMME_VALIDE.value:
            self._invalid_status()
        if training_case.trainer_id is None:
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté.")
        program = self.programs.get_by_case(case_id, for_update=True)
        if program is None:
            raise ApiError(404, "TRAINING_PROGRAM_NOT_FOUND", "Le programme est introuvable.")
        if not program.is_validated:
            raise ApiError(
                409,
                "TRAINING_PROGRAM_NOT_VALIDATED",
                "Le programme doit être validé.",
            )
        trainer = self.session.get(Trainer, training_case.trainer_id)
        if trainer is None:
            raise ApiError(409, "TRAINER_REQUIRED", "Le formateur affecté est introuvable.")
        day_count = len(program.days)
        duration_minutes = self._program_duration_minutes(program)
        trainer_cost, method = self._initial_trainer_cost(
            trainer.daily_rate,
            trainer.hourly_rate,
            day_count,
            duration_minutes,
        )
        pricing = TrainingPricing(
            training_case_id=case_id,
            trainer_cost=trainer_cost,
            transport_cost=Decimal("0.000"),
            room_cost=Decimal("0.000"),
            meal_cost=Decimal("0.000"),
            other_cost=Decimal("0.000"),
            margin_rate=Decimal("0.000"),
            vat_rate=Decimal("19.000"),
            trainer_daily_rate_snapshot=self._optional_money(trainer.daily_rate),
            trainer_hourly_rate_snapshot=self._optional_money(trainer.hourly_rate),
            program_day_count_snapshot=day_count,
            program_duration_minutes_snapshot=duration_minutes,
            trainer_cost_initialization_method=method.value,
        )
        try:
            self.pricings.add(pricing)
            training_case.status = TrainingCaseStatus.TARIFICATION_EN_PREPARATION.value
            self._log(
                administrator_id,
                training_case,
                pricing,
                "TrainingPricingCreated",
                {"initialization_method": method.value},
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ApiError(
                409,
                "TRAINING_PRICING_ALREADY_EXISTS",
                "Une tarification existe déjà pour ce dossier.",
            ) from exc
        return self.get(case_id)

    def update(
        self,
        case_id: UUID,
        payload: TrainingPricingUpdate,
        administrator_id: UUID,
    ) -> TrainingPricingResponse:
        training_case, pricing = self._editable(case_id)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field.endswith("_cost") and value is not None:
                value = quantize_money(value)
            elif field in {"margin_rate", "vat_rate"} and value is not None:
                value = value.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP)
            setattr(pricing, field, value)
        self._validate_vat(pricing)
        self._log(
            administrator_id,
            training_case,
            pricing,
            "TrainingPricingUpdated",
            {"fields": sorted(changes)},
        )
        self.session.commit()
        return self.get(case_id)

    def submit(self, case_id: UUID, administrator_id: UUID) -> TrainingPricingResponse:
        training_case, pricing = self._editable(case_id)
        self._ensure_dependencies(training_case)
        self._validate_financials(pricing)
        pricing.is_submitted = True
        pricing.submitted_at = datetime.now(UTC)
        pricing.return_reason = None
        training_case.status = TrainingCaseStatus.TARIFICATION_A_VALIDER.value
        self._log(
            administrator_id,
            training_case,
            pricing,
            "TrainingPricingSubmitted",
            {"new_status": training_case.status},
        )
        self.session.commit()
        return self.get(case_id)

    def return_to_preparation(
        self,
        case_id: UUID,
        reason: str,
        administrator_id: UUID,
    ) -> TrainingPricingResponse:
        training_case = self._get_case_for_change(case_id)
        pricing = self._get_pricing(case_id, for_update=True)
        if training_case.status != TrainingCaseStatus.TARIFICATION_A_VALIDER.value:
            self._invalid_status()
        if pricing.is_validated:
            self._already_validated()
        if not reason.strip():
            raise ApiError(400, "RETURN_REASON_REQUIRED", "Le motif du retour est obligatoire.")
        pricing.is_submitted = False
        pricing.submitted_at = None
        pricing.returned_at = datetime.now(UTC)
        pricing.return_reason = reason.strip()
        training_case.status = TrainingCaseStatus.TARIFICATION_EN_PREPARATION.value
        self._log(
            administrator_id,
            training_case,
            pricing,
            "TrainingPricingReturned",
            {"reason_provided": True, "new_status": training_case.status},
        )
        self.session.commit()
        return self.get(case_id)

    def validate(self, case_id: UUID, administrator_id: UUID) -> TrainingPricingResponse:
        training_case = self._get_case_for_change(case_id)
        pricing = self._get_pricing(case_id, for_update=True)
        if pricing.is_validated:
            self._already_validated()
        if (
            training_case.status != TrainingCaseStatus.TARIFICATION_A_VALIDER.value
            or not pricing.is_submitted
        ):
            self._invalid_status()
        self._ensure_dependencies(training_case)
        self._validate_financials(pricing)
        pricing.is_validated = True
        pricing.validated_at = datetime.now(UTC)
        training_case.status = TrainingCaseStatus.TARIFICATION_VALIDEE.value
        self._log(
            administrator_id,
            training_case,
            pricing,
            "TrainingPricingValidated",
            {"new_status": training_case.status},
        )
        self.session.commit()
        return self.get(case_id)

    def _editable(self, case_id: UUID) -> tuple[TrainingCase, TrainingPricing]:
        training_case = self._get_case_for_change(case_id)
        pricing = self._get_pricing(case_id, for_update=True)
        if (
            training_case.status != TrainingCaseStatus.TARIFICATION_EN_PREPARATION.value
            or pricing.is_submitted
            or pricing.is_validated
        ):
            raise ApiError(
                409,
                "TRAINING_PRICING_NOT_EDITABLE",
                "La tarification n’est pas modifiable dans son état actuel.",
            )
        return training_case, pricing

    def _ensure_dependencies(self, training_case: TrainingCase) -> None:
        if training_case.trainer_id is None:
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté.")
        program = self.programs.get_by_case(training_case.id)
        if program is None:
            raise ApiError(404, "TRAINING_PROGRAM_NOT_FOUND", "Le programme est introuvable.")
        if not program.is_validated:
            raise ApiError(
                409,
                "TRAINING_PROGRAM_NOT_VALIDATED",
                "Le programme doit rester validé.",
            )

    def _validate_financials(self, pricing: TrainingPricing) -> None:
        self._validate_vat(pricing)
        totals = self._totals(pricing)
        if (
            totals["total_costs"] <= 0
            or totals["total_excluding_tax"] <= 0
            or totals["total_including_tax"] <= 0
        ):
            raise ApiError(
                400,
                "TRAINING_PRICING_EMPTY",
                "La tarification doit contenir un montant strictement positif.",
            )

    @staticmethod
    def _validate_vat(pricing: TrainingPricing) -> None:
        if pricing.vat_rate not in ALLOWED_VAT_RATES:
            raise ApiError(
                400,
                "TRAINING_PRICING_INVALID_VAT_RATE",
                "Le taux de TVA sélectionné n’est pas autorisé.",
            )
        if (
            pricing.vat_rate == Decimal("0.000")
            and not (pricing.vat_exemption_reason or "").strip()
            and not (pricing.vat_legal_reference or "").strip()
        ):
            raise ApiError(
                400,
                "VAT_EXEMPTION_JUSTIFICATION_REQUIRED",
                "Une justification ou une référence fiscale est obligatoire pour une TVA à 0 %.",
            )

    def _response(self, pricing: TrainingPricing) -> TrainingPricingResponse:
        totals = self._totals(pricing)
        return TrainingPricingResponse(
            id=pricing.id,
            training_case_id=pricing.training_case_id,
            currency=pricing.currency,
            trainer_cost=quantize_money(pricing.trainer_cost),
            transport_cost=quantize_money(pricing.transport_cost),
            room_cost=quantize_money(pricing.room_cost),
            meal_cost=quantize_money(pricing.meal_cost),
            other_cost=quantize_money(pricing.other_cost),
            margin_rate=pricing.margin_rate.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP),
            vat_rate=pricing.vat_rate.quantize(RATE_QUANTUM, rounding=ROUND_HALF_UP),
            vat_exemption_reason=pricing.vat_exemption_reason,
            vat_legal_reference=pricing.vat_legal_reference,
            trainer_daily_rate_snapshot=pricing.trainer_daily_rate_snapshot,
            trainer_hourly_rate_snapshot=pricing.trainer_hourly_rate_snapshot,
            program_day_count_snapshot=pricing.program_day_count_snapshot,
            program_duration_minutes_snapshot=pricing.program_duration_minutes_snapshot,
            trainer_cost_initialization_method=TrainerCostInitializationMethod(
                pricing.trainer_cost_initialization_method
            ),
            is_submitted=pricing.is_submitted,
            submitted_at=pricing.submitted_at,
            is_validated=pricing.is_validated,
            validated_at=pricing.validated_at,
            returned_at=pricing.returned_at,
            return_reason=pricing.return_reason,
            editable=not pricing.is_submitted and not pricing.is_validated,
            created_at=pricing.created_at,
            updated_at=pricing.updated_at,
            **totals,
        )

    @staticmethod
    def _totals(pricing: TrainingPricing) -> dict[str, Decimal]:
        total_costs = quantize_money(
            pricing.trainer_cost
            + pricing.transport_cost
            + pricing.room_cost
            + pricing.meal_cost
            + pricing.other_cost
        )
        margin_amount = quantize_money(total_costs * pricing.margin_rate / Decimal("100"))
        total_excluding_tax = quantize_money(total_costs + margin_amount)
        vat_amount = quantize_money(total_excluding_tax * pricing.vat_rate / Decimal("100"))
        total_including_tax = quantize_money(total_excluding_tax + vat_amount)
        return {
            "total_costs": total_costs,
            "margin_amount": margin_amount,
            "total_excluding_tax": total_excluding_tax,
            "vat_amount": vat_amount,
            "total_including_tax": total_including_tax,
        }

    @staticmethod
    def _program_duration_minutes(program) -> int:
        total = 0
        for day in program.days:
            for item in day.items:
                if not any(child.parent_id == item.id for child in day.items):
                    total += item.theory_minutes + item.practice_minutes
        return total

    @staticmethod
    def _initial_trainer_cost(
        daily_rate: Decimal | None,
        hourly_rate: Decimal | None,
        day_count: int,
        duration_minutes: int,
    ) -> tuple[Decimal, TrainerCostInitializationMethod]:
        if daily_rate is not None:
            return (
                quantize_money(daily_rate * Decimal(day_count)),
                TrainerCostInitializationMethod.DAILY_RATE,
            )
        if hourly_rate is not None:
            return (
                quantize_money(hourly_rate * Decimal(duration_minutes) / Decimal("60")),
                TrainerCostInitializationMethod.HOURLY_RATE,
            )
        return Decimal("0.000"), TrainerCostInitializationMethod.NONE

    @staticmethod
    def _optional_money(value: Decimal | None) -> Decimal | None:
        return quantize_money(value) if value is not None else None

    def _get_case(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        return training_case

    def _get_case_for_change(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get_for_update(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        if training_case.is_archived:
            raise ApiError(409, "ARCHIVED_TRAINING_CASE", "Le dossier est archivé.")
        if training_case.status == TrainingCaseStatus.ANNULE.value:
            raise ApiError(409, "CANCELLED_TRAINING_CASE", "Le dossier est annulé.")
        return training_case

    def _get_pricing(self, case_id: UUID, *, for_update: bool = False) -> TrainingPricing:
        pricing = self.pricings.get_by_case(case_id, for_update=for_update)
        if pricing is None:
            raise ApiError(
                404,
                "TRAINING_PRICING_NOT_FOUND",
                "La tarification est introuvable.",
            )
        return pricing

    @staticmethod
    def _invalid_status() -> None:
        raise ApiError(
            409,
            "INVALID_TRAINING_CASE_STATUS",
            "Le statut du dossier ne permet pas cette action.",
        )

    @staticmethod
    def _already_validated() -> None:
        raise ApiError(
            409,
            "TRAINING_PRICING_ALREADY_VALIDATED",
            "La tarification est déjà validée.",
        )

    def _log(
        self,
        administrator_id: UUID,
        training_case: TrainingCase,
        pricing: TrainingPricing,
        action: str,
        extra: dict | None = None,
    ) -> None:
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                training_case_id=training_case.id,
                action=action,
                entity_type="training_pricing",
                entity_id=pricing.id,
                details={
                    "training_case_id": str(training_case.id),
                    "training_pricing_id": str(pricing.id),
                    **(extra or {}),
                },
            )
        )
