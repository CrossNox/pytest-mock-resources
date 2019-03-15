try:
    from unittest.mock import patch
except ImportError:
    from mock import patch  # type: ignore

import sqlparse
from decorator import decorator
from sqlalchemy import create_engine
from sqlalchemy.sql.elements import TextClause

from pytest_mock_resources.patch.redshift.mock_s3_copy import execute_mock_s3_copy_command, strip
from pytest_mock_resources.patch.redshift.mock_s3_unload import execute_mock_s3_unload_command


def substitute_execute_with_custom_execute(engine):
    """Substitute the default execute method with a custom execute for copy and unload command."""
    default_execute = engine.execute

    def custom_execute(statement, *args, **kwargs):
        if not isinstance(statement, TextClause) and strip(statement).lower().startswith("copy"):
            return execute_mock_s3_copy_command(statement, engine)
        if not isinstance(statement, TextClause) and strip(statement).lower().startswith("unload"):
            return execute_mock_s3_unload_command(statement, engine)
        return default_execute(statement, *args, **kwargs)

    def handle_multiple_statements(statement, *args, **kwargs):
        """Split statement into individual sql statements and execute.

        Splits multiple statements by ';' and executes each.
        NOTE: Only the result of the last statements is returned.
        """
        statements_list = parse_multiple_statements(statement)
        result = None
        for statement in statements_list:
            result = custom_execute(statement, *args, **kwargs)

        return result

    # Now each statement is handled as if it contains multiple sql statements
    engine.execute = handle_multiple_statements
    return engine


def parse_multiple_statements(statement):
    """Split the given sql statement into a list of individual sql statements."""
    statements_list = []

    # Ignore SQLAlchemy Text Objects.
    if isinstance(statement, TextClause):
        statements_list.append(statement)
        return statements_list

    # Prprocess input statement
    statement = _preprocess(statement)

    statements_list = [str(statement) for statement in sqlparse.split(statement)]

    return statements_list


def _preprocess(statement):
    """Preprocess the input statement."""
    statement = statement.strip()
    # Replace any occourance of " with '.
    statement = statement.replace('"', "'")
    if statement[-1] != ";":
        statement += ";"
    return statement


@decorator
def patch_create_engine(func, path=None, *args, **kwargs):
    if path is None:
        raise ValueError("Path cannot be None")

    with patch(path, new=mock_create_engine):
        return func(*args, **kwargs)


def mock_create_engine(*args, **kwargs):
    engine = create_engine(*args, **kwargs)
    return substitute_execute_with_custom_execute(engine)