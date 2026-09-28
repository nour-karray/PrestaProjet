# Migration contrôlée PostgreSQL vers MySQL

## Audit et mapping

| PostgreSQL historique | MySQL 8.x | Décision |
|---|---|---|
| `uuid` | `CHAR(36)` | Lisible, simple et compatible avec `java.util.UUID` |
| `jsonb` | `JSON` | Validation JSON native, sans opérateurs PostgreSQL |
| `numeric(p,s)` | `DECIMAL(p,s)` | `BigDecimal` côté Java, jamais `double` |
| `timestamp with time zone` | `DATETIME(6)` | Instants normalisés en UTC à l'entrée et à la migration |
| `date` | `DATE` | Sémantique inchangée |
| séquence du compteur annuel | ligne verrouillée + verrou MySQL | Références séquentielles conservées |
| index `lower(name)` | collation `utf8mb4_0900_ai_ci` + unicité sur `name` | Recherche et unicité insensibles à la casse |
| index partiel du contact principal | colonne générée `primary_guard` | Un seul contact principal par entreprise |
| index partiels des items | colonnes de portée générées | Ordres module/sous-module conservés |
| Alembic | baseline MySQL différée | Aucun historique PostgreSQL rejoué aveuglément |

Le schéma MySQL complet est dans `database/mysql-init/001-schema.sql`. Hibernate
reste en `ddl-auto=validate`; aucune table n'est créée ou modifiée au démarrage.

## Données existantes

La base PostgreSQL locale contient des données dans les domaines métier ; elle
ne doit donc pas être supprimée. Le script
`scripts/migrate-postgresql-to-mysql.py` copie les tables dans l'ordre des clés
étrangères, refuse une cible non vide et compare le nombre de lignes après chaque
table. Il ne supprime ni ne modifie aucune ligne source.

Installer l'extra ponctuel de migration puis définir localement les deux URL :

```powershell
pip install -e ".\backend-python[migration]"
$env:SOURCE_POSTGRES_DATABASE_URL="postgresql+psycopg://..."
$env:TARGET_MYSQL_DATABASE_URL="mysql+pymysql://.../trainflow?charset=utf8mb4"
python scripts/migrate-postgresql-to-mysql.py
python scripts/migrate-postgresql-to-mysql.py --verify-only
```

Ne retirez la base PostgreSQL historique qu'après une vérification réussie des
comptages et des parcours Auth, Companies et Contacts sur MySQL.

## Flyway

Flyway n'est pas activé pendant cette bascule. Une baseline MySQL sera créée
seulement après stabilisation des entités principales. L'historique Alembic est
conservé dans Git à titre historique tant que le backend FastAPI existe.
