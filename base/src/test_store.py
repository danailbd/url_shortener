import pytest

from .store import InMemoryStore, DuplicateRecordError, URL_SCHEMA
# xxx could use mocked version instead to avoid coupling
from .models import UrlEntity

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

