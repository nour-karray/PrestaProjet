# Démarrage avec Docker

Docker est optionnel. Pour le développement courant sous Windows, consultez
plutôt [local-development.md](local-development.md).

## Configuration

```powershell
Copy-Item .env.example .env
```

Remplacez tous les marqueurs `<...>`. Les valeurs indispensables sont
`MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` et `JWT_SECRET`.

Laissez `SEED_DEMO_DATA=false` sauf si vous souhaitez explicitement créer un
administrateur de démonstration.

## Construction et démarrage

```powershell
docker compose config -q
docker compose build
docker compose up -d
docker compose ps
```

MySQL initialise un volume neuf avec `database/mysql-init/001-schema.sql`.
Les backends ne lancent aucune migration et Hibernate reste en validation seule.
Les services par défaut sont accessibles sur :

- frontend : http://localhost:3000 ;
- API FastAPI : http://localhost:8000 ;
- OpenAPI : http://localhost:8000/docs ;
- santé Spring Boot : http://localhost:8080/health ;
- MySQL : localhost:3306.

Les ports hôtes peuvent être changés avec `FRONTEND_HOST_PORT`,
`BACKEND_HOST_PORT` et `MYSQL_HOST_PORT`.

## Diagnostic et arrêt

```powershell
docker compose logs --tail 100 trainflow-backend-python trainflow-backend trainflow-frontend mysql
docker compose down
```

`docker compose down` conserve le volume MySQL. N'ajoutez `-v` que si vous
voulez réellement supprimer les données Docker.

