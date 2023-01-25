import pytest

from fastapi import status
from fastapi.testclient import TestClient

from .main import app
from .main import UrlEntity, InMemoryStore, DuplicateRecordError, get_db, URL_SCHEMA


client = TestClient(app)


# setup
# get
# add
# last
class TestInMemoryStore:
    # @pytest.fixture
    # def mock_schema():
    #     return { "tab": { "tab_ids": [], "tabs_data": {} } }

    def test_in_memory_store_add(self):
        store = InMemoryStore(URL_SCHEMA)

        store.add(UrlEntity(id=1, original_url="some"))

        assert store.get_storage() == {'urls': {'url_ids': [1], 'urls_data': {1: {'id': 1, 'original_url': 'some'}}}}

    def test_in_memory_store_add_duplicate(self):
        store = InMemoryStore(URL_SCHEMA)

        store.add(UrlEntity(id=1, original_url="some"))

        with pytest.raises(DuplicateRecordError) as ex:
            store.add(UrlEntity(id=1, original_url="some1"))

    def test_in_memory_store_get_existing(self):
        store = InMemoryStore(URL_SCHEMA)

        store.add(UrlEntity(id=1, original_url="some"))

        result = store.get(UrlEntity, 1)
        assert result.id == 1
        assert result.original_url == "some"

    # TODO parametarize
    def test_in_memory_store_get_non_existent(self):
        store = InMemoryStore(URL_SCHEMA)

        assert store.get(UrlEntity, 1) == None

    @pytest.mark.skip()
    def test_in_memory_store_singleton(self):
        store = InMemoryStore.instance(URL_SCHEMA)
        store.add(UrlEntity(id=1, original_url="some1"))

        store = InMemoryStore.instance(URL_SCHEMA)
        store.add(UrlEntity(id=2, original_url="some2"))

        assert store.get(UrlEntity, 1).original_url == "some1"
        assert store.get(UrlEntity, 2).original_url == "some2"
        assert store.get(UrlEntity, 3) == None

        # Teardown
        store.flush()

    def test_flush_clears_store(self):
        # Given
        store = InMemoryStore(URL_SCHEMA)
        store.add(UrlEntity(id=1, original_url="some"))
        
        # When
        store.flush()

        # Then
        assert store.get_storage()["urls"]["url_ids"] == []
        assert store.get_storage()["urls"]["urls_data"] == {}

    def test_last(self):
        store = InMemoryStore(URL_SCHEMA)
        store.add(UrlEntity(id=1, original_url="some1"))

        assert store.last(UrlEntity).original_url == "some1"

        store.add(UrlEntity(id=2, original_url="some2"))

        assert store.last(UrlEntity).original_url == "some2"


class TestUrlApi:
    def teardown(self):
        # TODO Abstract/decouple
        InMemoryStore.instance(URL_SCHEMA).flush()

    def test_create_url(self):
        response = client.post(
            '/urls',
            json={"original_url": "some.com"}
        )

        assert response.json() == {"id": "1", "original_url": "some.com"}


    @pytest.fixture
    def mocked_store(self):
        store = InMemoryStore.instance(URL_SCHEMA)
        store.add(UrlEntity(id="1", original_url="https://some.com"))

    def test_redirect_url(self, mocked_store):
        response = client.get(f"/1", allow_redirects=False)
        assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
        assert response.headers["location"] == "https://some.com"
