import importlib
import types
import pytest
from fastapi.testclient import TestClient


class DummyCursor:
    def __init__(self, fetchone_value=(b"dummy_mvt",)):
        self.queries = []
        self.fetchone_value = fetchone_value

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchone(self):
        return self.fetchone_value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyConn:
    def __init__(self, cursor: DummyCursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture()
def app_module(monkeypatch):
    mod = importlib.import_module("app.main")
    importlib.reload(mod)
    mod._tile_cache.clear()
    dummy_cursor = DummyCursor(fetchone_value=(b"dummy_mvt",))
    dummy_conn = DummyConn(dummy_cursor)
    monkeypatch.setattr(mod, "get_db_connection", lambda: dummy_conn)
    mod._test_dummy_cursor = dummy_cursor
    return mod


@pytest.fixture()
def client(app_module):
    return TestClient(app_module.app)
