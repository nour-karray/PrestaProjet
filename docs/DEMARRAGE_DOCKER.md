# Démarrage avec Docker

Docker est optionnel. Pour le développement courant sous Windows, consultez
plutôt [DEMARRAGE_LOCAL.md](DEMARRAGE_LOCAL.md).

## Configuration

```powershell
Copy-Item .env.example .env
```

Remplacez tous les marqueurs `<...>`. Les valeurs indispensables sont
`POSTGRES_PASSWORD`, `JWT_SECRET`, `DATABASE_URL` et `DATABASE_URL_DOCKER`.
Dans `DATABASE_URL_DOCKER`, l'hôte doit être `postgres`, et non `localhost`.

Laissez `SEED_DEMO_DATA=false` sauf si vous souhaitez explicitement créer un
administrateur de démonstration.

## Construction et démarrage

```powershell
docker compose config -q
docker compose build
docker compose up -d
docker compose ps
```

Le backend applique automatiquement les migrations Alembic avant de démarrer.
Les services par défaut sont accessibles sur :

- frontend : http://localhost:3000 ;
- API : http://localhost:8000 ;
- OpenAPI : http://localhost:8000/docs ;
- PostgreSQL : localhost:5432.

Les ports hôtes peuvent être changés avec `FRONTEND_HOST_PORT`,
`BACKEND_HOST_PORT` et `POSTGRES_HOST_PORT`.

## Diagnostic et arrêt

```powershell
docker compose logs --tail 100 backend frontend postgres
docker compose down
```

`docker compose down` conserve le volume PostgreSQL. N'ajoutez `-v` que si vous
voulez réellement supprimer les données Docker.

