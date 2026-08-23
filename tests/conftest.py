from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from sesame.config import Config
from sesame.repository.db import DatabaseConnection

from tests.helpers import FakeEntropySource


@pytest.fixture
def fake_entropy_source() -> FakeEntropySource:
    """A deterministic entropy source with a single default value."""
    return FakeEntropySource()


@pytest.fixture
def tmp_config_dir(tmp_path) -> str:
    """Isolated directory to use as a Config's config_path, never touching
    the real src/sesame/config/config.toml file."""
    return str(tmp_path / "config")


@pytest.fixture
def make_config(tmp_config_dir):
    """Factory fixture to build a Config instance pointed at a tmp dir."""

    def _make_config(config_path: str | None = None) -> Config:
        return Config(config_path=config_path or tmp_config_dir)

    return _make_config


@pytest.fixture
def config_instance(make_config) -> Config:
    return make_config()


@pytest.fixture
def db_path(tmp_path) -> str:
    return str(tmp_path / "vault.db")


@pytest.fixture
def fake_db_config(db_path):
    """A minimal stand-in for Config exposing only what DatabaseConnection needs."""
    return SimpleNamespace(vault_db_path=db_path)


@pytest.fixture
def database_connection(fake_db_config) -> DatabaseConnection:
    connection = DatabaseConnection(config=fake_db_config)
    yield connection
    connection.conn.close()


@pytest.fixture
def vault_key() -> bytes:
    return os.urandom(32)


@pytest.fixture
def mock_console() -> MagicMock:
    console = MagicMock()
    console.input = MagicMock(return_value="")
    return console
