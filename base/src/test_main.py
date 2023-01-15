from fastapi import status
from fastapi.testclient import TestClient

from .main import app


client = TestClient(app)


def test_create_url():
    response = client.post(
        '/urls',
        json={"original_url": "some.com"}
    )


    assert response.json() == {"id": "1", "original_url": "some.com"}


def test_redirect_url():
    response = client.get(
        '/urls/ag',
        json={"original_url": "some.com"}
    )

    assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
    assert response.headers == True
