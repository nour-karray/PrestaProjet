# Base PostgreSQL portable

Le fichier `prestacode-schema.sql` contient la structure complète de PostgreSQL.
`alembic-version.sql` conserve la version des migrations. Les données de
démonstration sont générées par le script officiel du projet. Aucun texte de CV,
document stocké, mot de passe local ou renseignement personnel n’est publié.

## Restauration

Créer une base vide puis exécuter :

```powershell
psql -h localhost -U prestacode -d prestacode -f database\prestacode-schema.sql
psql -h localhost -U prestacode -d prestacode -f database\alembic-version.sql
```

Générer ensuite les données de démonstration :

```powershell
cd backend
$env:SEED_DEMO_DATA="true"
$env:DEMO_ADMIN_EMAIL="admin@formation.local"
$env:DEMO_ADMIN_PASSWORD="Admin123!"
.\.venv\Scripts\python.exe -m app.db.seed
```

Le compte généré est :

- email : `admin@formation.local`
- mot de passe : `Admin123!`

Pour appliquer de futures migrations après restauration :

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Les fichiers `.env`, `storage/`, les CV originaux et les documents générés ne
doivent pas être publiés dans le dépôt.
