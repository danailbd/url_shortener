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
    @pytest.fixture(scope="function")
    def store(self):
        return InMemoryStore(URL_SCHEMA)

    class TestAdd:
        def test_add_should_insert_a_record_properly(self, store):
            store.add(UrlEntity(id=1, original_url="some"))

            assert store.get_storage() == {'urls': {'url_ids': [1], 'urls_data': {1: {'id': 1, 'original_url': 'some'}}}}

        def test_add_should_raise_an_exception_on_duplicate_records(self, store):
            store.add(UrlEntity(id=1, original_url="some"))

            with pytest.raises(DuplicateRecordError) as ex:
                store.add(UrlEntity(id=1, original_url="some1"))

    def test_get_should_return_the_correct_record(self, store):
        store.add(UrlEntity(id=1, original_url="some"))

        result = store.get(UrlEntity, 1)
        assert result.id == 1
        assert result.original_url == "some"

    # TODO parametarize
    def test_get_returns_none_when_record_not_found(self, store):
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

    def test_flush_clears_the_store(self, store):
        # Given
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
