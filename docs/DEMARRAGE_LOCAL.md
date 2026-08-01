# Démarrage local sans Docker

Ce mode démarre PostgreSQL, le backend et le frontend directement sous Windows.

## Prérequis

- Python 3.12 ;
- Node.js 20.9 ou supérieur ;
- PostgreSQL 12 ou supérieur ;
- une base et un rôle PostgreSQL dédiés à l'application.

## Configuration

Depuis la racine du projet :

```powershell
Copy-Item .env.example .env
```

Dans `.env`, remplacez tous les marqueurs `<...>`. `DATABASE_URL` doit viser
`localhost`, par exemple :

```dotenv
DATABASE_URL=postgresql+psycopg://prestacode:mot_de_passe@localhost:5432/prestacode
```

Si le port `5432` est déjà occupé (par exemple par Odoo), démarrez PostgreSQL
sur un autre port, puis utilisez ce port dans `DATABASE_URL`. Générez un
`JWT_SECRET` aléatoire d'au moins 32 caractères. Ne versionnez jamais `.env`.

Le compte de démonstration est désactivé par défaut. Pour en créer un :

```dotenv
SEED_DEMO_DATA=true
DEMO_ADMIN_EMAIL=votre-adresse@example.test
DEMO_ADMIN_PASSWORD=<mot_de_passe_robuste>
```

## Installation initiale

```powershell
.\setup-local.cmd
```

Cette commande installe les dépendances, applique les migrations et exécute le
seed. Si `SEED_DEMO_DATA=false`, aucune donnée de démonstration n'est créée.

## Démarrage

```powershell
.\start-local.cmd
```

Ou manuellement, dans un premier terminal :

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m app.db.seed
python -m uvicorn app.main:app --reload --port 8000
```

Puis dans un second terminal :

```powershell
cd frontend
npm install
npm run dev
```

Ouvrez http://localhost:3000. Vérifiez l'API avec
http://localhost:8000/health ; la réponse attendue est `{"status":"ok"}`.

## Arrêt

Utilisez `Ctrl+C` dans chaque terminal. PostgreSQL peut ensuite être arrêté avec
l'outil ou le service Windows utilisé pour le lancer.

