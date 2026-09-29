-- TrainFlow AI historical schema baseline.
-- Existing installations are baselined at this version by Flyway, so this
-- file is not executed against them. It intentionally contains no DDL: this
-- phase must not recreate, alter, or delete existing tables.
-- New local databases still use database/mysql-init/001-schema.sql first.
SELECT 1;
