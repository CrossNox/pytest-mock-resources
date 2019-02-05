# Schireson Pytest Mock-Resources

#schiresonip #ruby

## Introduction

Pytest Mock-Resources is a collection of convenient pytest plugins to make it easier to test against code that depends on external resourcess.

Currently available resources:

* Mock Postgres
* Mock Redshift
* Mock SQLite

## Installing

    pip install --index-url https://artifactory.schireson.com/artifactory/api/pypi/pypi/simple "pytest-mock-resources[postgres]"

## Mock Redshift and Postgres

## Configuration

If you need to construct your own connection or client in any test, the following config can be used:

    username: "user"
    password: "password"
    host: Use PG_HOST fixture
    port: Use PG_PORT fixture
    database: database_name you passed into the create_*_fixture function

### Running the tests in CircleCI

Make sure to add the following section to ALL jobs that will be running tests with `redshift` or `postgres` fixtures or you will receive a `ContainerCheckFailed: Unable to connect to [...] Postgres test container` error.

    jobs:
      <YOUR JOB NAME>:
          docker:
          - image: <IMAGE>  // schireson/cicd-python... circleci/python:2.7.14... etc
          - image: postgres:9.6.10-alpine
              environment:
              POSTGRES_DB: dev
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
          steps:
          - checkout
          ...


## Example

### Basic Example

    # src/package/models.py:

    from sqlalchemy import Column, Integer
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class User(Base):
        __tablename__ = "user"
        __table_args__ = {"schema": "stuffs"}

        id = Column(Integer, primary_key=True, autoincrement=True)


    # tests/conftest.py:

    from package.models import User  # These models could be imported from ANYWHERE
    from pytest_mock_resources import create_redshift_fixture, Rows

    rows = Rows(
        User(name="Harold"),
        User(name="Catherine"),
    )

    redshift = create_redshift_fixture(
        rows,
    )


    # tests/test_something.py:

    def test_something_exists(redshift):
        execute = redshift.execute("SELECT * FROM user")

        result = sorted([row[0] for row in execute])
        assert ["Catherine", "Harold"] == result

### Statements Example

    # tests/conftest.py:

    from pytest_mock_resources import create_redshift_fixture, Statements

    statements = Statements(
        """
        CREATE TABLE account(
         user_id serial PRIMARY KEY,
         username VARCHAR (50) UNIQUE NOT NULL,
         password VARCHAR (50) NOT NULL
        );
        """,
        """
        INSERT INTO account VALUES (1, 'user1', 'password1')
        """,
    )

    redshift = create_redshift_fixture(
        statements,
    )


    # tests/test_something.py:

    def test_something_exists(redshift):
        execute = redshift.execute("SELECT password FROM account")

        result = sorted([row[0] for row in execute])
        assert ["password1"] == result

### DDL Only Example

There may be a case where you don't leverage SQLAlchemy's ORM layer but still define a database's DDL following the SQLAlchemy Expressions API. An example of this is the [client-redshift-schema](https://github.com/schireson/client-redshift-schema) package.

For these cases, instantiate the desired fixture with the metadata as an argument.

    # tests/conftest.py:

    from pytest_mock_resources import create_redshift_fixture, Statements
    from client_redshift_schema import meta
    from client_redshift_schema.warehouse import warehouse_stacked_data

    statements = Statements(
        warehouse_stacked_data.insert().values(network="ABCDE"),
    )

    redshift = create_redshift_fixture(
        meta,
        statements,
    )


    # tests/test_something.py:

    def test_something_exists(redshift):
        execute = redshift.execute("SELECT network FROM warehouse.warehouse_stacked_data")

        result = sorted([row[0] for row in execute])
        assert ["ABCDE"] == result

### Custom Connection Example

    # tests/conftest.py:

    import pytest

    from package.models import User
    from pytest_mock_resources import create_redshift_fixture, Rows

    rows = Rows(
        User(name="Jolteon"),
    )

    redshift = create_redshift_fixture(
        rows,
        # NOTE: A Database Name must be provided in the case where you need to create your own connection object.
        database_name="SOMETHING_MEMORABLE"
    )


    # tests/test_something.py:

    from sqlalchemy import create_engine


    def test_something_exists(PG_HOST, PG_PORT, redshift):
        engine = create_engine(
            "postgresql://{username}:{password}@{host}:{port}/{database}?sslmode=disable".format(
                database="SOMETHING_MEMORABLE",
                user="user",
                password="password",
                host=PG_HOST,
                port=PG_PORT,
            ),
            isolation_level="AUTOCOMMIT",
        )

        engine.execute = redshift_ordered_actions.execute("SELECT * FROM user")

        result = sorted([row[0] for row in execute])
        assert ["Jolteon"] == result

## Contributing Pre-Requisites

* [Lucha](https://github.com/schireson/lucha/) must be globally installed (preferably via pipx) to run most MakeFile commands.

## Running the tests

* Running the unit tests: `pytest` or `make test`
* Running the linters: `make lint`

## Changing the dependencies

### Adding a new dependency

Add the requirements to the relevant package's `deps/requirements.in` or `deps/dev-requirements.in`
then (inside the package's folder) run:

    make sync-deps

### Synchronizing your virtualenv with the requirements

    make install-deps

### Updating an existing dependency

    pip-compile --upgrade-package docker
