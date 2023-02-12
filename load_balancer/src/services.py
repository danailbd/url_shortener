from .store import BaseStore, InMemoryStore, URL_SCHEMA
from .models import BaseHashGenerator, NaiveHashGenerator, UrlEntity

class UrlService:
    def __init__(
            self,
            store: BaseStore = InMemoryStore.instance(URL_SCHEMA),
            hash_strategy: BaseHashGenerator = NaiveHashGenerator
    ):
        self.store = store
        self.hash_strategy = hash_strategy

    def create(self, original_url: str) -> UrlEntity:
        last: UrlEntity = self.store.last(UrlEntity)
        last_id: str = last.id if last else ''

        new_id = self.hash_strategy.generate_hash(original_url, str(last_id))

        entity = UrlEntity(id=new_id, original_url=original_url)
        self.store.add(entity)

        return entity

    # Simple delegator
    def get(self, id: str) -> UrlEntity | None:
        return self.store.get(UrlEntity, id=id)