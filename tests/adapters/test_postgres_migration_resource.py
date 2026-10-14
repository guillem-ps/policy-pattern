"""
Verifies the packaged PostgreSQL migration resource is present and loadable.

Reads the resource via importlib.resources, the same way a consumer's
migration tooling would. No database needed. This proves the resource
loads correctly in the current environment; it does not independently
verify the file is included in a *built* wheel/sdist artifact — that
would need a separate build-and-inspect step, not covered here.
"""

from importlib.resources import files

from pytest import mark


@mark.unit
def test_migration_resource_exists_and_is_loadable() -> None:
    """
    Test that the versioned migration resource loads via importlib.resources and contains the expected DDL.
    """
    sql = files("policy_pattern").joinpath("sql", "postgres", "0001_create_policy_tuples.sql").read_text()

    assert "CREATE TABLE" in sql
    assert '"authz_tuples"' in sql
    ddl_body = sql[sql.index("CREATE TABLE") :]
    assert ddl_body.count('COLLATE "C"') == 6
