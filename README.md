# Gestion des formations professionnelles

Application web de gestion du cycle de formation professionnelle :
entreprises, contacts, dossiers, formateurs, besoins, programmes,
tarification et documents PDF.

## Architecture

- `backend/` : API FastAPI, SQLAlchemy, Alembic et PostgreSQL ;
- `frontend/` : Next.js, TypeScript et App Router ;
- `storage/` : CV et documents générés, exclus de Git ;
- `docs/` : documentation fonctionnelle, technique et d'exploitation.

## Démarrage

Le mode local sans Docker est le mode conseillé pour le développement Windows :

- [Démarrage local sans Docker](docs/DEMARRAGE_LOCAL.md)
- [Démarrage avec Docker](docs/DEMARRAGE_DOCKER.md)

Copiez d'abord `.env.example` vers `.env`, puis remplacez tous les marqueurs
`<...>`. Aucun identifiant administrateur n'est fourni dans le dépôt. La création
d'un compte de démonstration est facultative et nécessite explicitement
`SEED_DEMO_DATA=true`, `DEMO_ADMIN_EMAIL` et `DEMO_ADMIN_PASSWORD`.

## URLs par défaut

- Frontend : http://localhost:3000
- API : http://localhost:8000
- OpenAPI : http://localhost:8000/docs
- Santé : http://localhost:8000/health

## Vérifications

Backend :

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app
```

Tests PostgreSQL réels, uniquement sur une base dédiée dont le nom se termine
par `_test` :

```powershell
$env:POSTGRES_TEST_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/prestacode_test"
.\.venv\Scripts\python.exe -m pytest -q tests/integration_postgres
```

Frontend :

```powershell
cd frontend
npm run lint
npm test -- --run
npm run build
npm run test:e2e
```

Le test E2E exige `E2E_ADMIN_EMAIL` et `E2E_ADMIN_PASSWORD` ainsi qu'une
application locale déjà démarrée.

## Sécurité et stabilisation

- [Phase de stabilisation](docs/PHASE_STABILISATION.md)
- [Audit de sécurité](docs/STABILISATION_SECURITE.md)

Les secrets, bases locales, environnements virtuels, dépendances, sorties de
tests, CV et documents générés sont exclus de Git.

