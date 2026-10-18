"""Verify the packaged PostgreSQL migration creates the expected schema."""

from psycopg_pool import ConnectionPool
from pytest import mark


@mark.integration
@mark.slow
def test_migrated_table_matches_schema_contract(postgres_pool: ConnectionPool) -> None:
    """Check the actual PostgreSQL columns, primary key, and collations."""
    with postgres_pool.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull,
                      COALESCE(coll.collname, '')
               FROM pg_attribute a
               LEFT JOIN pg_collation coll ON coll.oid = a.attcollation
               WHERE a.attrelid = 'authz_tuples'::regclass AND a.attnum > 0 AND NOT a.attisdropped
               ORDER BY a.attnum"""
        )
        columns = cursor.fetchall()

        cursor.execute(
            """SELECT array_agg(a.attname ORDER BY key.ordinality)
               FROM pg_constraint con
               CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS key(attnum, ordinality)
               JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = key.attnum
               WHERE con.conrelid = 'authz_tuples'::regclass AND con.contype = 'p'"""
        )
        primary_key = cursor.fetchone()

    expected_names = ["object_type", "object_id", "relation", "subject_type", "subject_id", "subject_relation"]
    assert [column[0] for column in columns] == expected_names
    assert all(column[1] == "text" and column[2] for column in columns)
    assert all(column[3] == "C" for column in columns)
    assert primary_key == (expected_names,)
