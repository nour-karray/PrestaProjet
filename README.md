# TrainFlow AI

**AI-assisted Training Management Platform**

TrainFlow AI gère le cycle complet d’une formation professionnelle : entreprises,
contacts, formateurs et CV, dossiers, besoins, programmes assistés par IA,
tarification et documents PDF.

## Architecture active

- `frontend/` : React, TypeScript et Vite, port 5173 ;
- `backend/` : Spring Boot 3 / Java 21, port 8080 ;
- MySQL 8 : persistance, migrations Flyway et validation Hibernate ;
- Ollama : `qwen2.5:1.5b` pour les CV et `qwen2.5:3b` pour les programmes ;
- `storage/` : CV et documents générés, contenu exclu de Git.

## Démarrage

1. Copier `.env.example` vers `.env` et renseigner les valeurs locales.
2. Démarrer MySQL et Ollama.
3. Exécuter `setup-local.cmd`, puis `start-local.cmd`.

Documentation :

- [Architecture](docs/architecture.md)
- [Développement local](docs/local-development.md)
- [Pipeline IA](docs/ai-cv-pipeline.md)
- [Sécurité](docs/security.md)
- [Tests](docs/testing.md)

Aucun identifiant administrateur n’est fourni. Les données de démonstration
restent désactivées par défaut (`SEED_DEMO_DATA=false`).

Demo credentials are not provided in the repository. Define your own values before enabling demo data seeding.

## Vérifications

```powershell
cd backend
mvn test
mvn package

cd ..\frontend
npm run lint
npm test
npm run build
npm run test:e2e
```

Le parcours E2E nécessite une application locale démarrée et les variables
`E2E_ADMIN_EMAIL` et `E2E_ADMIN_PASSWORD` définies hors Git.

Les secrets, bases locales, sorties de build, CV et documents générés sont
exclus du dépôt.
