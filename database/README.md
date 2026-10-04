# Base MySQL portable

Le schéma courant de TrainFlow AI est géré par Flyway dans
`backend/src/main/resources/db/migration/`. Il cible MySQL 8.x, utilise
`CHAR(36)` pour les UUID, `JSON`, `DECIMAL` et des timestamps UTC en
`DATETIME(6)`.

Pour initialiser une base locale vide, définissez les variables MySQL puis
démarrez le backend Spring Boot :

```powershell
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3307"
$env:MYSQL_DATABASE="trainflow"
$env:MYSQL_USER="<your-local-user>"
$env:MYSQL_PASSWORD="<your-local-password>"
mvn -f backend/pom.xml spring-boot:run
```

Le dossier `archive/` conserve les exports PostgreSQL historiques. Ils ne sont
pas exécutés par l'application et ne doivent pas être importés dans MySQL.

Pour conserver les données existantes, suivez
[`docs/mysql-migration.md`](../docs/mysql-migration.md) et utilisez le script de
copie non destructif avant d'arrêter l'ancienne base.

Flyway est actif dans le backend Spring avec une baseline non destructive à la
version `20260923.0017`. Une base vide reçoit le schéma complet via la migration
de baseline. Une installation historique non vide est marquée à cette version :
aucune table métier n'est recréée. Hibernate reste configuré exclusivement avec
`ddl-auto=validate`.
