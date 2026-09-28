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

## MySQL

Le schéma `database/mysql-init/001-schema.sql` contient les statuts résilients
du pipeline. Hibernate valide ce schéma sans le modifier.

## Limite OCR

Le service OCR est un point d’intégration explicite. Aucun moteur OCR système
n’est livré avec l’application : sans moteur local configuré, le pipeline
bascule en revue manuelle avec `OCR_FAILED`.

## Ollama

Ollama fonctionne localement et reste externe aux conteneurs applicatifs.

```powershell
ollama serve
ollama pull qwen2.5:1.5b
ollama list
```

Configuration actuelle :

```dotenv
LOCAL_LLM_URL=http://127.0.0.1:11434
CV_LLM_MODEL=qwen2.5:1.5b
CV_LLM_KEEP_ALIVE=30s
LOCAL_LLM_MODEL=qwen-prestacode-v3:latest
LOCAL_LLM_TIMEOUT_SECONDS=600
```

Le modèle léger analyse les CV. Le modèle spécialisé génère les programmes.
L'identifiant historique du modèle de programme reste inchangé pour préserver
la compatibilité avec l'installation Ollama existante.

## Vérifications

Configurer une base dédiée dont le nom se termine par `_test` :

```powershell
$env:MYSQL_TEST_DATABASE_URL="mysql+pymysql://USER:PASSWORD@localhost:3306/trainflow_test?charset=utf8mb4"
cd backend-python
pytest -q tests/integration_mysql
```

La suite vérifie le schéma, la conservation du texte, la panne LLM, le
retry, l'absence de formateur avant revue, la validation humaine et le lien
entre le CV et le formateur.

Scénario manuel : importer un PDF, vérifier `REVIEW_REQUIRED`, interrompre
Ollama puis contrôler le fallback manuel. Après redémarrage, « Réessayer
l'analyse » doit conserver le même identifiant de CV et le texte extrait.

