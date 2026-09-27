import os

import pytest

from app.ai.local_llm import OllamaLocalLLMClient
from app.services.trainer_cv_extractor import TrainerCVExtractor

pytestmark = [
    pytest.mark.local_llm,
    pytest.mark.skipif(
        os.getenv("RUN_LOCAL_LLM_TEST") != "1",
        reason="Test du modèle local désactivé par défaut.",
    ),
]


def test_private_local_model_with_synthetic_cv() -> None:
    text = """CV de démonstration sans donnée réelle.
Nom : Camille Démonstration
Email : camille.demo@example.test
Téléphone : +33 6 00 00 00 00
Fonction : Formatrice en management
Compétences : communication, leadership
"""
    result = TrainerCVExtractor(OllamaLocalLLMClient()).extract(text)
    assert result.full_name == "Camille Démonstration"
    assert result.email == "camille.demo@example.test"
