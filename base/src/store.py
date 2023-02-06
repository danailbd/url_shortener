import copy

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
        self._storage = copy.deepcopy(self._schema)

 
    def get_storage(self) -> dict:
        return self._storage

    def _setup_storage(self, schema):
        print("Storage setup")
        # Not the best having things look the same
        self._storage = copy.deepcopy(schema)

    def _get_table(self, entity_cls): return self._storage[entity_cls.table_name]

