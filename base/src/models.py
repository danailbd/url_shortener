from .store import BaseEntity

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
class UrlEntity(BaseEntity):
    table_name="urls"
    table_keys="url_ids"
    table_data="urls_data"

    id: str
    original_url: str