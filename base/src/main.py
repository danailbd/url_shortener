import copy

from fastapi import Depends, FastAPI, Response, Path, status
from fastapi.responses import RedirectResponse
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
    table_keys="url_ids"
    table_data="urls_data"

    id: str
    original_url: str

# ---

URL_SCHEMA = {
            # Simulate a table hash index-like behavior. Keep a ids lists
            # so that we can access the last key
            # <table>: {
            #          <table>_ids: [],
            #          <table>_data: {}
            # }
            "urls": {
                "url_ids": [],
                "urls_data": {}
            }
        }

class BaseStore:
    _store_instance = None
    # TODO move out
    _schema: dict = {}

    def __init__(self, schema):
        self._schema = schema
        self._setup_storage(schema)

    @classmethod
    def instance(cls, *args):
        if not cls._store_instance:
            cls._store_instance = cls(*args)

        return cls._store_instance

    def add(self, entity: BaseEntity):
        pass

    def get(self, entity_cls: BaseEntity, id: str) -> BaseEntity | None:
        pass

    def last(self, entity_cls: BaseEntity):
        pass

    def _setup_storage():
        pass


class DuplicateRecordError(Exception):
    pass
class InMemoryStore(BaseStore):
    # TODO use this abstraction 
    _storage: dict

    def add(self, entity: BaseEntity) -> None:
        table = self._get_table(type(entity))

        if self.get(entity_cls=type(entity), id=entity.id):
            raise DuplicateRecordError()

        table[entity.table_keys].append(entity.id)
        table[entity.table_data][entity.id] = vars(entity)

    def get(self, entity_cls: BaseEntity, id: str) -> BaseEntity | None:
        table = self._get_table(entity_cls)
        if id in table[entity_cls.table_data]:
            return entity_cls(**table[entity_cls.table_data][id])
        return None

    def last(self, entity_cls: BaseEntity) -> BaseEntity | None:
        table = self._get_table(entity_cls)
        if len(table[entity_cls.table_keys]) == 0:
            return None

        last_key: int = table[entity_cls.table_keys][-1]
        return entity_cls(**table[entity_cls.table_data][last_key])
 
    def flush(self):
        self._storage = self._schema

 
    def get_storage(self) -> dict:
        return self._storage

    def _setup_storage(self, schema):
        print("Storage setup")
        # Not the best having things look the same
        self._storage = copy.deepcopy(schema)

    def _get_table(self, entity_cls): return self._storage[entity_cls.table_name]

class UrlService:
    def __init__(
            self,
            store: BaseStore = InMemoryStore.instance(URL_SCHEMA),
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
    def get(self, id: str) -> UrlEntity | None:
        return self.store.get(UrlEntity, id=id)

app = FastAPI()

class Url(BaseModel):
    original_url: str

def get_db():
    return InMemoryStore.instance(URL_SCHEMA)

@app.post("/urls")
async def create_url(
        url: Url,
        store: BaseStore = Depends(get_db)
):
    # TODO validate
    url_entity = UrlService(store).create(original_url=url.original_url)

    # TODO use pydantic model instead
    return vars(url_entity)

@app.get("/")
async def read_root():
    return Response("Hello, it's me. Yet another Url Shortener")

@app.get("/{short_url}")
async def redirect_url(
        short_url: str = Path(title="Shorthand for the url", default=""),
        store: BaseStore = Depends(get_db)
):
    # TODO validate
    url_entity = UrlService(store).get(id=short_url)

    if url_entity:
        return RedirectResponse(
            url_entity.original_url,
            status_code=status.HTTP_301_MOVED_PERMANENTLY
        )
    return Response(status_code=status.HTTP_404_NOT_FOUND)