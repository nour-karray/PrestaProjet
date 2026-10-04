# Persistance MySQL

MySQL 8 est l’unique base active de TrainFlow AI. Spring Boot utilise le driver
MySQL, Flyway applique les migrations versionnées et Hibernate valide le schéma
avec `ddl-auto=validate`.

Les variables locales sont `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`,
`MYSQL_USER`, `MYSQL_PASSWORD` et les équivalents `SPRING_DATASOURCE_*`.
Aucun secret ne doit être versionné.

L’ancienne migration depuis PostgreSQL est terminée. Son contexte reste décrit
dans les documents de `docs/archive/`; aucun outil de migration Python n’est
requis au runtime.
