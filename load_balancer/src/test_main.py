import pytest

from fastapi import status
from fastapi.testclient import TestClient

from .main import app
from .models import UrlEntity
from .store import InMemoryStore, URL_SCHEMA


client = TestClient(app)

class TestUrlApi:
    def teardown_method(self):
        # TODO Abstract/decouple
        InMemoryStore.instance(URL_SCHEMA).flush()

    @pytest.fixture
    def setup_store(self):
        store = InMemoryStore.instance(URL_SCHEMA)
        store.add(UrlEntity(id="1", original_url="https://some.com"))

    class TestUrlApi:
        def test_create_url_returns_a_created_record(self):
            response = client.post(
                '/urls',
                json={"original_url": "http://some.com"}
            )

            assert response.json() == {"id": "1", "original_url": "http://some.com"}
        
        def test_create_url_error_on_invalid_url(self):
            response = client.post(
                '/urls',
                json={"original_url": "some.com"}
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert response.text == '{"detail":[{"loc":["body","original_url"],"msg":"invalid or missing URL scheme","type":"value_error.url.scheme"}]}'

    def test_redirect_url(self, setup_store):
        response = client.get(f"/1", allow_redirects=False)

        assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
        assert response.headers["location"] == "https://some.com"
