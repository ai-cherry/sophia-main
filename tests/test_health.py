import json
import sys
from types import ModuleType

import pytest
from flask import Blueprint

# Stub out heavy route modules before importing the app
for name, bp_name, path in [
    ("backend.app.routes.company_routes", "company_bp", "/overview"),
    (
        "backend.app.routes.strategy_routes",
        "strategy_bp",
        "/growth-opportunities",
    ),
    ("backend.app.routes.operations_routes", "operations_bp", "/api/operations/dummy"),
]:
    mod = ModuleType(name)
    bp = Blueprint(bp_name, __name__)

    from flask_jwt_extended import jwt_required

    @bp.route(path)
    @jwt_required()
    def _endpoint():  # pragma: no cover - minimal stub
        return "ok"

    setattr(mod, bp_name, bp)
    sys.modules[name] = mod

# Real auth routes are used

from backend.app.main import create_app, check_database, check_redis


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint_success(monkeypatch, client):
    monkeypatch.setattr("backend.app.main.check_database", lambda: True)
    monkeypatch.setattr("backend.app.main.check_redis", lambda: True)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["components"]["database"] == "connected"
    assert data["components"]["cache"] == "connected"


def test_health_endpoint_failure(monkeypatch, client):
    monkeypatch.setattr("backend.app.main.check_database", lambda: False)
    monkeypatch.setattr("backend.app.main.check_redis", lambda: False)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["components"]["database"] == "unreachable"
    assert data["components"]["cache"] == "unreachable"


class DummyConn:
    def close(self):
        pass


def test_check_database(monkeypatch):
    def success_connect(*args, **kwargs):
        return DummyConn()

    monkeypatch.setattr("psycopg2.connect", success_connect)
    assert check_database() is True

    def fail_connect(*args, **kwargs):
        raise Exception("db error")

    monkeypatch.setattr("psycopg2.connect", fail_connect)
    assert check_database() is False


def test_check_redis(monkeypatch):
    class DummyRedis:
        def ping(self):
            return True

        def close(self):
            pass

    monkeypatch.setattr("redis.Redis.from_url", lambda *a, **k: DummyRedis())
    assert check_redis() is True

    def fail_from_url(*args, **kwargs):
        raise Exception("redis error")

    monkeypatch.setattr("redis.Redis.from_url", fail_from_url)
    assert check_redis() is False
