# TrainFlow AI

**AI-assisted Training Management Platform**

Application web de gestion du cycle de formation professionnelle :
entreprises, contacts, dossiers, formateurs, besoins, programmes,
tarification et documents PDF.

## Architecture

- `backend/` : socle Spring Boot de migration, exposé temporairement sur le port 8080 ;
- `backend-python/` : API FastAPI historique, toujours utilisée par le frontend sur le port 8000 ;
- `frontend/` : Next.js, TypeScript et App Router ;
- `storage/` : CV et documents générés, exclus de Git ;
- `docs/` : documentation fonctionnelle, technique et d'exploitation.

## Démarrage

Le mode local sans Docker est le mode conseillé pour le développement Windows :

- [Architecture](docs/architecture.md)
- [Démarrage local sans Docker](docs/local-development.md)
- [Démarrage avec Docker](docs/docker.md)
- [Pipeline IA et CV](docs/ai-cv-pipeline.md)

Copiez d'abord `.env.example` vers `.env`, puis remplacez tous les marqueurs
`<...>`. Aucun identifiant administrateur n'est fourni dans le dépôt. La création
d'un compte de démonstration est facultative et nécessite explicitement
`SEED_DEMO_DATA=true`, `DEMO_ADMIN_EMAIL` et `DEMO_ADMIN_PASSWORD`.
Demo credentials are not provided in the repository. Define your own values before enabling demo data seeding.

## URLs par défaut

- Frontend : http://localhost:3000
- API : http://localhost:8000
- OpenAPI : http://localhost:8000/docs
- Santé : http://localhost:8000/health
- Santé Spring Boot (Phase 1) : http://localhost:8080/health

## Vérifications

Backend :

```powershell
cd backend-python
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app
```

Socle Spring Boot :

```powershell
cd backend
mvn test
mvn package
```

Tests PostgreSQL réels, uniquement sur une base dédiée dont le nom se termine
par `_test` :

```powershell
$env:POSTGRES_TEST_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/trainflow_test"
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

- [Sécurité](docs/security.md)
- [Archives techniques](docs/archive/)

Les secrets, bases locales, environnements virtuels, dépendances, sorties de
tests, CV et documents générés sont exclus de Git.

