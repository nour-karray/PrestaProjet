# Architecture de TrainFlow AI

## État transitoire — Phase 3

```text
Next.js / React / TypeScript
        ↓ REST API :8000
FastAPI historique (backend-python/)
        ↓
PostgreSQL

Spring Boot (backend/) :8080
        ├── GET /health
        ├── Auth / Security
        └── Companies / Contacts protégés
```

Le frontend continue d'utiliser FastAPI pendant la migration. Le nouveau
backend Spring Boot expose désormais l'authentification compatible FastAPI et
protège Companies/Contacts. Flyway, PDF et Ollama restent hors périmètre.

## Cible backend

Le backend cible est un monolithe modulaire Java 21 organisé par domaine :

```text
com.trainflow
├── auth
├── company
├── trainer
├── trainingcase
├── trainingneed
├── program
├── pricing
├── document
├── ai
├── security
└── shared
```

Les contrôleurs portent HTTP, les services les règles métier, les repositories
la persistance et les DTO les contrats REST. Les entités JPA ne seront pas
exposées directement.

## PostgreSQL

La base existante reste la source de vérité. Spring mappe uniquement
`administrators`, `companies` et `company_contacts`. Hibernate utilise `ddl-auto=validate`,
`generate-ddl=false` et `spring.sql.init.mode=never` : aucune table ou migration
n'est créée. Flyway sera introduit ultérieurement avec une baseline correspondant
au schéma Alembic existant.

## Compatibilité Companies / Contacts

Les routes, statuts fonctionnels, champs JSON en `snake_case`, pagination,
archivage logique, contact principal et enveloppes d'erreur reprennent FastAPI.
La protection par JWT en cookies HttpOnly est active côté Spring. Le frontend
reste néanmoins branché sur FastAPI `:8000` pendant cette phase de migration.

## Compatibilité

Les routes, structures JSON en `snake_case`, cookies et codes d'erreur FastAPI
sont conservés progressivement. Aucun domaine autre que l'authentification et
Companies/Contacts n'est exposé par Spring pendant cette phase.
