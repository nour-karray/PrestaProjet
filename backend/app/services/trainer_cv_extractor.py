import re

from pydantic import ValidationError

from app.ai.local_llm import LocalLLMClient
from app.core.config import settings
from app.core.errors import ApiError
from app.schemas.company import validate_local_email
from app.schemas.cv_extraction import TrainerCVExtractionResult

PROMPT_TEMPLATE = """Tu extrais des informations structurées depuis un CV.
Analyse uniquement le texte délimité ci-dessous et retourne uniquement un objet JSON.
Respecte strictement le schéma fourni par le serveur. Aucun Markdown ni explication.
N'invente aucune information. Utilise null pour les champs absents et des listes vides.
Conserve les noms propres et les formulations réellement présentes.
Signale toute ambiguïté dans warnings.
Pour les coordonnées, respecte exactement les libellés du document :
- "Téléphone" alimente phone ;
- "GSM" ou "Mobile" alimente mobile_phone.
Ne place jamais une date, un numéro CIN ou un numéro de passeport dans un champ téléphone.
Sépare "Date et lieu de naissance" entre birth_date et birth_place.
Ne déduis pas une entreprise actuelle sans preuve et ne calcule pas arbitrairement
les années d'expérience. Ne transforme pas une compétence implicite en compétence
explicite. Ne confonds pas une école avec une entreprise, une mission avec un poste,
et ne mélange pas plusieurs expériences.

--- DÉBUT DU TEXTE DU CV ---
{cv_text}
--- FIN DU TEXTE DU CV ---
"""
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d ()/.-]{7,}\d)(?!\w)")
URL_PATTERN = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)


class TrainerCVExtractor:
    def __init__(self, llm_client: LocalLLMClient) -> None:
        self.llm_client = llm_client

    def extract(self, text: str) -> TrainerCVExtractionResult:
        if len(text.strip()) < 40:
            raise ApiError(422, "CV_TEXT_NOT_USABLE", "Le texte du CV n’est pas exploitable.")
        prompt_text, technical_warning = _limit_text(text)
        response = self.llm_client.generate_structured(
            PROMPT_TEMPLATE.format(cv_text=prompt_text),
            TrainerCVExtractionResult,
        )
        try:
            result = TrainerCVExtractionResult.model_validate(response)
        except ValidationError as exc:
            raise ApiError(
                502,
                "JSON_VALIDATION_FAILED",
                "La réponse du modèle local ne respecte pas le schéma attendu.",
            ) from exc
        updated = _apply_deterministic_fallback(result, text)
        if technical_warning and technical_warning not in updated.warnings:
            updated.warnings.append(technical_warning)
        return updated


def extract_labeled_identity(text: str) -> TrainerCVExtractionResult:
    """Extract the identity block of structured CVs without invoking the LLM."""
    return _apply_deterministic_fallback(TrainerCVExtractionResult(), text)


def _limit_text(text: str) -> tuple[str, str | None]:
    limit = max(settings.local_llm_max_tokens * 2, 4_000)
    if len(text) <= limit:
        return text, None
    head_size = int(limit * 0.75)
    tail_size = limit - head_size
    truncated = f"{text[:head_size]}\n\n[SECTION INTERMÉDIAIRE OMISE]\n\n{text[-tail_size:]}"
    return truncated, "Le texte a été limité pour respecter la capacité configurée du modèle."


def _apply_deterministic_fallback(
    result: TrainerCVExtractionResult, text: str
) -> TrainerCVExtractionResult:
    changes: dict[str, str] = {}
    if result.email is None:
        match = EMAIL_PATTERN.search(text)
        if match:
            try:
                email = validate_local_email(match.group())
            except ValueError:
                email = None
            if email:
                changes["email"] = email
    full_name = _label_value(text, r"Nom\s+et\s+Prénom", ["Nationalité", "Date et lieu de Naissance"])
    if result.full_name is None and full_name:
        changes["full_name"] = full_name
    birth = _label_value(text, r"Date\s+et\s+lieu\s+de\s+Naissance", [r"N.?CIN/Passeport", "Mail"])
    if birth:
        birth_parts = re.split(r"\s+à\s+", birth, maxsplit=1, flags=re.IGNORECASE)
        if result.birth_date is None:
            changes["birth_date"] = birth_parts[0]
        if result.birth_place is None and len(birth_parts) == 2:
            changes["birth_place"] = birth_parts[1]
    labeled_phone = _label_value(text, "Téléphone", ["Public", "Privé", "Indépendant"])
    labeled_mobile = _label_value(text, r"(?:GSM|Mobile)", ["Adresse", "Téléphone"])
    if result.phone is None and labeled_phone:
        changes["phone"] = _clean_phone(labeled_phone)
    if result.mobile_phone is None and labeled_mobile:
        changes["mobile_phone"] = _clean_phone(labeled_mobile)
    address = _label_value(text, "Adresse", ["Employeur actuel"])
    if result.address is None and address:
        changes["address"] = address
    employer = _label_value(text, "Employeur actuel", ["Adresse de l.employeur"])
    if result.company is None and employer:
        changes["company"] = employer
    employer_address = _label_value(
        text, r"Adresse\s+de\s+l.employeur", ["Téléphone", "Public", "Privé"]
    )
    if result.employer_address is None and employer_address:
        changes["employer_address"] = employer_address
    urls = URL_PATTERN.findall(text)
    if result.linkedin_url is None:
        linkedin = next((url for url in urls if "linkedin.com/" in url.lower()), None)
        if linkedin:
            changes["linkedin_url"] = linkedin.rstrip(".,;")
    if result.website is None:
        website = next((url for url in urls if "linkedin.com/" not in url.lower()), None)
        if website:
            changes["website"] = website.rstrip(".,;")
    return result.model_copy(update=changes)


def _label_value(text: str, label: str, following_labels: list[str]) -> str | None:
    stops = "|".join(f"(?:{value})" for value in following_labels)
    match = re.search(
        rf"(?:^|\s)(?:{label})\s*:\s*(.+?)(?=\s+(?:{stops})\s*:|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    value = " ".join(match.group(1).split()).strip(" ,;-")
    return value or None


def _clean_phone(value: str) -> str:
    match = PHONE_PATTERN.search(value)
    return " ".join((match.group() if match else value).split())
