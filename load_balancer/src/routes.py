import heapq
import asyncio
import random

from fastapi import APIRouter, Depends, Response, Request, status
from pydantic import BaseModel, HttpUrl, Field


router = APIRouter()

# Ex. sequence
# B - i1 --> n1++
# B - i2 --> n2++
#  --n2 <-- i2
# B - i3 --> n2++
#  --n1 <-- i1
#  --n2 <-- i3


# TODO rename
class BrokerRequest:
    id: int
    pass

class NodeResponse:
    pass

# basic pub/sub
class Emitter:
    class Event:
        pass

    _subscribers: dict[str, list[function]] = {}

    def on(self, event, callback):
        if not self._subscribers[event]:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
    
    # rename publish / emit
    def emit(self, event):
        if not self._subscribers[event]:
            return

        for sub_callback in self._subscribers[event]:
            # notify with Node
            sub_callback(self)


# TODO use
class NodeTimeout(Exception):
    pass

class Node(Emitter):
    class Event:
        ActiveRequestsChanged = 'active_request_changed'

    id: int
    uri: str
    active_requests: int = 0

    def __init__(self, _id, _uri):
        self.id = _id
        self.uri = _uri

    async def process_request(self, request: BrokerRequest) -> NodeResponse:
        # keep internal queue?
        # return await client.send(request)
        # TODO move to func/class 
        self.active_requests += 1
        self.emit(Node.Event.ActiveRequestsChanged)

        try:
            # XXX testing only
            await asyncio.sleep(random.randrange(0, 10 + self.active_requests))
        except:
            pass
        finally:
            self.active_requests -= 1
            self.emit(Node.Event.ActiveRequestsChanged)
    
    # TODO
    async def health_check():
        pass

    # XXX no, Node shouldn't know about priority ; it should be an user's responsibility
    # e.g. NodeWrapper
    def __lt__(self, other):
        return self.active_requests < other.active_requests

# TODO in config / env vars
NODES_LIST: list[Node] = [
    Node(1, 'localhost:3001'),
    Node(2, 'localhost:3002'),
]

class Singleton:
    @classmethod
    def instance(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

# Manages the priority of nodes / balances nodes load
# ?Follow-ups on node freeze?
# NodesLoadBalancer #get_least_busy_node #rebalance
class NodesLoadTracker(Singleton):
    # Keep a sorted heap
    _nodes_heap: list[Node]

    def __init__(self, nodes: list[Node] = NODES_LIST):
        self._nodes_heap = nodes
        self._attach_node_load_listener()

    def get_least_busy_node(self) -> Node:
        self._nodes_heap[0]

    # protected

    # TODO speed up - rebalance(node) & move the node up or down in a tree/heap;
    # heapify would be O(n)
    def _rebalance_nodes(self, node) -> None:
        heapq.heapify(self._nodes_heap)

    def _attach_node_load_listener(self) -> None:
        # subscribe
        for node in self._nodes_heap:
            node.on(Node.Events.ActiveRequestsChanged, self._rebalance_nodes)


class RequestBroker(Singleton):
    def __init__(self, nodes_load_tracker: NodesLoadTracker = NodesLoadTracker.instance()):
        self._nodes_load_tracker = nodes_load_tracker

    # TODO keep some requests queue/list/set/tree?
    async def process_request(self, request: BrokerRequest) -> Response:
        try:
            node = self._nodes_load_tracker.get_least_busy_node()
            resp = await node.process_request(request)
        except:
            # NodeProcessError
            pass # TODO
            return None
        else:
            return resp



def get_request_broker():
    return RequestBroker.instance()


@router.route("/{full_path:path}")
async def forward_request(
    request: Request,
    full_path: str,
    request_broker: RequestBroker = Depends(get_request_broker)
):
    # RequestParallelBroker
    resp = await request_broker.process_request(request, full_path)

    return resp

router.get("/")


async def read_root():
    return Response("Hello, it's me. A simple LoadBalancer")
