import pytest

from fastapi import status
from fastapi.testclient import TestClient

from httpx import Response

from .routes import RequestBroker, NodesLoadTracker, Node, NodeResponse
from ..main import app

class MockNode(Node):
    async def process_request(self, request):
        return NodeResponse(self.id, Response(200))


# --- conftest.py
from typing import Any
from typing import Generator
from fastapi import FastAPI

from .routes import get_request_broker

@pytest.fixture #(scope="function")
def client() -> Generator[TestClient, Any, None]:
    """
    """

    # TODO make configurable
    def _get_request_broker(self):
        return RequestBroker(nodes_load_tracker=NodesLoadTracker(nodes=[MockNode(1, '')]))

    app.dependency_overrides[get_request_broker] = _get_request_broker
    with TestClient(app) as client:
        yield client


class TestApi:
    class TestGetForwarding:
        def test_basic_forward_given_single_worker(self, client):
            # XXX fix "self" query param requirement
            response = client.get("/a?self=1")

            assert response.status_code == status.HTTP_200_OK



# Ex. sequence
# B - i1 --> n1++
# B - i2 --> n2++
#  --n2 <-- i2
# B - i3 --> n2++
#  --n1 <-- i1
#  --n2 <-- i3


# class TestRequestBroker:

#     async def test_create_url_returns_a_created_record(self):
#         broker = RequestBroker.instance()
        
#         fake_request = {}

#         await broker.process_request(fake_request)
#         await broker.process_request(fake_request)
#         await broker.process_request(fake_request)
#         await broker.process_request(fake_request)