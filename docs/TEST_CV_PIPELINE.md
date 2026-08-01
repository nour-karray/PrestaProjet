# Tests du pipeline CV

## PostgreSQL

Configurer une base dédiée dont le nom se termine par `_test` :

```powershell
$env:POSTGRES_TEST_DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/prestacode_test"
pytest -q tests/integration_postgres
```

La suite vérifie les migrations, la conservation du texte, la panne LLM, le
retry, l’absence de formateur avant revue, la validation humaine et le lien
entre le CV et le formateur.

## Validations complètes

```powershell
cd backend
python -m compileall app tests
pytest -q
ruff check .
mypy app
alembic current
alembic heads
alembic history

cd ..\frontend
npm run lint
npm run test -- --run
npm run build
```

## Scénario manuel

Importer un PDF, vérifier `REVIEW_REQUIRED`, arrêter Ollama, relancer
l’analyse et contrôler `LLM_UNAVAILABLE`. Redémarrer Ollama, utiliser
« Réessayer l’analyse », puis vérifier que le même identifiant de CV et le
texte extrait sont conservés. La création n’est autorisée qu’après validation
explicite du formulaire.
