# Base PostgreSQL portable

Le fichier `trainflow-schema.sql` contient la structure complète de PostgreSQL.
`alembic-version.sql` conserve la version des migrations. Les données de
démonstration sont générées par le script officiel du projet. Aucun texte de CV,
document stocké, mot de passe local ou renseignement personnel n’est publié.

## Restauration

Créer une base vide puis exécuter :

```powershell
psql -h localhost -U trainflow -d trainflow -f database\trainflow-schema.sql
psql -h localhost -U trainflow -d trainflow -f database\alembic-version.sql
```

Générer ensuite les données de démonstration :

```powershell
cd backend-python
$env:SEED_DEMO_DATA="true"
$env:DEMO_ADMIN_EMAIL="demo@example.test"
$env:DEMO_ADMIN_PASSWORD="<choose-a-strong-password>"
.\.venv\Scripts\python.exe -m app.db.seed
```

Demo credentials are not provided in the repository. Define your own values before enabling demo data seeding.

Pour appliquer de futures migrations après restauration :

```powershell
cd backend-python
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Les fichiers `.env`, `storage/`, les CV originaux et les documents générés ne
doivent pas être publiés dans le dépôt.
