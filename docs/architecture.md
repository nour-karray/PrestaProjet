# Architecture de TrainFlow AI

## État transitoire — Phase 1

```text
Next.js / React / TypeScript
        ↓ REST API :8000
FastAPI historique (backend-python/)
        ↓
PostgreSQL

Spring Boot (backend/) :8080
        └── GET /health
```

Le frontend continue d'utiliser FastAPI pendant la migration. Le nouveau
backend Spring Boot est un socle minimal sans domaine métier, authentification,
Flyway, PDF ou Ollama.

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

La base existante reste la source de vérité. En phase 1, l'initialisation
DataSource/JPA de Spring est explicitement désactivée, car aucune entité n'est
encore migrée. Les paramètres préparatoires restent non destructifs
(`ddl-auto=none`, `generate-ddl=false`, `spring.sql.init.mode=never`). Aucune
connexion, table ou migration n'est créée. Flyway sera introduit ultérieurement
avec une baseline correspondant au schéma Alembic existant.

## Compatibilité

Les routes, structures JSON en `snake_case`, cookies et codes d'erreur FastAPI
seront conservés progressivement. Aucun endpoint métier n'est exposé par Spring
pendant cette phase.
