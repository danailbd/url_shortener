import pytest

from fastapi import status
from fastapi.testclient import TestClient

# from .main import app

# client = TestClient(app)
# class TestUrlApi:
#     def teardown_method(self):
#         # TODO Abstract/decouple
#         InMemoryStore.instance(URL_SCHEMA).flush()

#     @pytest.fixture
#     def setup_store(self):
#         store = InMemoryStore.instance(URL_SCHEMA)
#         store.add(UrlEntity(id="1", original_url="https://some.com"))

#     def test_redirect_url(self, setup_store):
#         response = client.get(f"/1", allow_redirects=False)

#         assert response.status_code == status.HTTP_301_MOVED_PERMANENTLY
#         assert response.headers["location"] == "https://some.com"



from .routes import RequestBroker



# Ex. sequence
# B - i1 --> n1++
# B - i2 --> n2++
#  --n2 <-- i2
# B - i3 --> n2++
#  --n1 <-- i1
#  --n2 <-- i3


class TestRequestBroker:

    async def test_create_url_returns_a_created_record(self):
        broker = RequestBroker.instance()
        
        fake_request = {}

        await broker.process_request(fake_request)
        await broker.process_request(fake_request)
        await broker.process_request(fake_request)
        await broker.process_request(fake_request)