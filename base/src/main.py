# import psycopg2
from fastapi import FastAPI, Response, Path
from fastapi.responses import RedirectResponse
from typing import Annotated
from pydantic import BaseModel

# Strategy
class BaseHashGenerator:
    @staticmethod
    def generate_hash(str: str, prefix: str=""):
        pass

class NaiveHashGenerator(BaseHashGenerator):
    @staticmethod
    def generate_hash(str: str, prefix: str=""):
        # simply use the current id, that should be unique
        # TODO optimize ; use bytes
        return prefix + '1'


# Defines a schema for the entity
class BaseEntity:
    table_name: str
    table_keys: str
    table_data: str

    id: str

    def __init__(self, **dict):
        for property in dict:
            if not property in self.__annotations__:
                raise TypeError(f"Property not defined: {property}")
            setattr(self, property, dict[property])

class UrlEntity(BaseEntity):
    table_name="urls"
    table_keys="url_keys"
    table_data="urls_data"

    id: str
    original_url: str


class BaseStore:
    _store_instance = None

    def __init__(self):
        self._setup_storage()

    @classmethod
    def instance(cls):
        if not cls._store_instance:
            cls._store_instance = cls()

        return cls._store_instance

    def add(self, entity: BaseEntity):
        pass

    def get(self, entity_cls: BaseEntity, id: str):
        pass

    def last(self, entity_cls: BaseEntity):
        pass

    def _setup_storage():
        pass


class InMemoryStore(BaseStore):
    # TODO use this abstraction 
    storage: dict
    schema = {
            # Simulate a table with a hash index, so that we can access
            # the last key
            "urls": {
                "url_keys": [],
                "urls_data": {}
            }
        }

    def add(self, entity: BaseEntity) -> None:
        table = self._get_table(type(entity))

        table[entity.table_keys].append(entity.id)
        table[entity.table_data][entity.id] = vars(entity)

    def get(self, entity_cls: BaseEntity, id: str) -> BaseEntity:
        table = self._get_table(entity_cls)
        return table[entity_cls.table_data][id]

    def last(self, entity_cls: BaseEntity) -> BaseEntity | None:
        table = self._get_table(entity_cls)
        if len(table[entity_cls.table_keys]) == 0:
            return None

        last_key: int = table[entity_cls.table_keys][-1]
        return table[entity_cls.table_data][last_key]
 

    def _setup_storage(self):
        print("Storage setup")
        # Not the best having things look the same
        self.storage = type(self).schema

    def _get_table(self, entity_cls):
        return self.storage[entity_cls.table_name]


class UrlService:
    def __init__(
            self,
            store: BaseStore = InMemoryStore.instance(),
            hash_strategy: BaseHashGenerator = NaiveHashGenerator
    ):
        self.store = store
        self.hash_strategy = hash_strategy

    def create(self, original_url: str) -> BaseEntity:
        last: UrlEntity = self.store.last(UrlEntity)
        last_id: str = last.id if last else ''

        new_id = self.hash_strategy.generate_hash(original_url, str(last_id))

        entity = UrlEntity(id=new_id, original_url=original_url)
        self.store.add(entity)

        return entity

    # Simple delegator
    def get(self, id: str) -> UrlEntity:
        self.store.get(UrlEntity, id)

app = FastAPI()

class Url(BaseModel):
    original_url: str


@app.post("/urls")
async def create_url(url: Url):
    # TODO validate
    url_entity = UrlService().create(original_url=url.original_url)

    # TODO use pydantic model instead
    return vars(url_entity)

@app.get("/")
async def read_root():
    return Response("Hello, it's me. Yet another Url Shortener")

# url_id
@app.get("/{short_url}")
async def redirect_url(
    short_url: str = Path(title="Shorthand for the url", default="")
):
    # TODO validate
    url_entity = UrlService().get(id=short_url)
    return RedirectResponse(url_entity.original_url)