"""Smoke tests — verify the package is installed correctly and the app boots."""

from fastapi.testclient import TestClient

import fems
from fems.main import app


def test_package_version() -> None:
    assert fems.__version__ == "0.1.0"


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
