# Pipeline CV opérationnel

## Pipeline

1. validation du PDF ou DOCX ;
2. stockage du fichier ;
3. extraction native du texte ;
4. OCR seulement lorsque le texte est insuffisant ;
5. contrôle d’Ollama et du modèle via `/api/tags` ;
6. génération d’un JSON strict ;
7. validation Pydantic ;
8. formulaire de revue humaine ;
9. création du formateur après confirmation explicite.

Statuts : `UPLOADED`, `TEXT_EXTRACTED`, `OCR_REQUIRED`, `OCR_COMPLETED`,
`AI_ANALYSIS_PENDING`, `AI_ANALYSIS_COMPLETED`, `REVIEW_REQUIRED`,
`VALIDATED`, `FAILED`.

Erreurs : `FILE_INVALID`, `FILE_TOO_LARGE`, `PDF_ENCRYPTED`,
`TEXT_EXTRACTION_EMPTY`, `OCR_FAILED`, `LLM_UNAVAILABLE`, `LLM_TIMEOUT`,
`LLM_MODEL_NOT_FOUND`, `LLM_INVALID_RESPONSE`, `JSON_VALIDATION_FAILED`.

Une panne Ollama conserve le fichier et le texte. L’administrateur peut
réessayer l’analyse, continuer manuellement ou choisir un autre fichier.
Le retry réutilise le même import et le texte déjà extrait.

## PostgreSQL

Les migrations doivent être appliquées jusqu’à `20260730_0012`. La migration
0012 corrige la contrainte PostgreSQL des statuts sans modifier la migration
0011 déjà appliquée.

## Limite OCR

Le service OCR est un point d’intégration explicite. Aucun moteur OCR système
n’est livré avec l’application : sans moteur local configuré, le pipeline
bascule en revue manuelle avec `OCR_FAILED`.

