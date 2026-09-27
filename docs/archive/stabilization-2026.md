# Phase de stabilisation

## Périmètre

Cette phase consolide l'application existante sans ajouter de fonctionnalité
métier, de page, de table, de workflow, d'OCR, de RAG, d'e-mail ou d'automatisation.

## Travaux réalisés

1. dépôt Git isolé à la racine de `trainflow-ai` et règles d'exclusion renforcées ;
2. configuration PostgreSQL explicite pour le local et Docker ;
3. migrations Alembic validées jusqu'à la révision `20260725_0010` ;
4. correction complète du typage statique backend ;
5. ajout de la protection frontend pour toutes les routes `/formateurs` ;
6. tests d'intégration sur une vraie base PostgreSQL dédiée ;
7. parcours E2E navigateur couvrant le cycle complet d'un dossier ;
8. durcissement des secrets, du seed, des fichiers et de l'authentification ;
9. construction et exécution validées avec Docker Compose ;
10. documentation séparée pour le local sans Docker et Docker.

## Validation effectuée

- MyPy : aucune erreur sur 85 fichiers source ;
- Ruff : aucune erreur ;
- migrations : schéma au head et cohérent avec les modèles ;
- PostgreSQL réel : relations, contraintes, transactions et cinq PDF ;
- frontend : lint, tests, build de production et proxy ;
- E2E : connexion, création des données, transitions, tarification, documents et clôture ;
- Docker : PostgreSQL, backend et frontend sains, endpoints HTTP accessibles.

## Principes conservés

PostgreSQL reste la source de vérité. Les fichiers binaires restent hors de la
base et hors de Git. Les migrations précèdent toujours le démarrage de l'API.
Le seed est optionnel et sans secret fourni par le dépôt.

