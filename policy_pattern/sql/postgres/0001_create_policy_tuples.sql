-- Initial schema for PostgresTupleStore (policy_pattern/adapters/postgres.py).
--
-- By default, apply this through your own migration tooling (Alembic, a
-- raw-SQL migration step, etc.). PostgresTupleStore can optionally run
-- this statement at construction with auto_create_schema=True. See
-- docs/architecture.md's "Database Adapters" section.

CREATE TABLE IF NOT EXISTS "authz_tuples" (
    object_type       TEXT NOT NULL COLLATE "C",
    object_id         TEXT NOT NULL COLLATE "C",
    relation          TEXT NOT NULL COLLATE "C",
    subject_type      TEXT NOT NULL COLLATE "C",
    subject_id        TEXT NOT NULL COLLATE "C",
    subject_relation  TEXT NOT NULL DEFAULT '' COLLATE "C",
    PRIMARY KEY (object_type, object_id, relation, subject_type, subject_id, subject_relation)
);
