from typing import Dict

from fastapi.testclient import TestClient

from app.core.config import settings


def test_celery_worker_test(client: TestClient, _token_headers: Dict[str, str]) -> None:
    data = {"msg": "test"}
    r = client.post(
        f"{settings.API_V1_STR}/utils/test-celery/",
        json=data,
        headers=_token_headers,
    )
    response = r.json()
    assert response["msg"] == "Word received"
