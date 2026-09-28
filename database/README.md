# Base MySQL portable

Le schéma courant de TrainFlow AI se trouve dans
`mysql-init/001-schema.sql`. Il cible MySQL 8.x, utilise `CHAR(36)` pour les
UUID, `JSON`, `DECIMAL` et des timestamps UTC en `DATETIME(6)`.

Pour initialiser une base locale vide :

```powershell
cmd /c "mysql -h localhost -P 3306 -u trainflow -p trainflow ^< database\mysql-init\001-schema.sql"
```

Le dossier `archive/` conserve les exports PostgreSQL historiques. Ils ne sont
pas exécutés par l'application et ne doivent pas être importés dans MySQL.

Pour conserver les données existantes, suivez
[`docs/mysql-migration.md`](../docs/mysql-migration.md) et utilisez le script de
copie non destructif avant d'arrêter l'ancienne base.

Flyway n'est pas encore actif. Hibernate utilise exclusivement
`ddl-auto=validate`.
