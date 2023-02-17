import heapq
import httpx
import asyncio
import random

import logging

from fastapi import APIRouter, Depends, Response, Request, status
# from pydantic import BaseModel, HttpUrl, Field

logger = logging.getLogger('routes')

router = APIRouter()


DISABLE_NODE_REQUESTS = False


class BrokerRequest:
    last_id: int = 0

    id: int
    request: Request

    def __init__(self, request):
        self.request = request
        # TODO could be generator?
        self.id = BrokerRequest.next_id()

    @classmethod
    def next_id(cls):
        # TODO or use uuid
        cls.last_id += 1
        return cls.last_id


class NodeResponse:
    def __init__(self, node_id: int, options: dict):
        self.worker_id = node_id
        self.opts = options

# basic pub/sub


class Emitter:
    class Event:
        pass

    _subscribers: dict  # dict[str, list[Callable]] = {}

    def __init__(self):
        self._subscribers = {}

    def on(self, event, callback):
        if event not in self._subscribers:
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


# TODO rename: Worker/WorkerNode/ServiceNode/
class Node(Emitter):
    class Event:
        ActiveRequestsChanged = 'active_request_changed'

    id: int
    uri: str
    active_requests: int = 0

    def __init__(self, _id, _uri):
        super().__init__()

        self.id = _id
        self.uri = _uri

    async def process_request(self, request: BrokerRequest) -> NodeResponse:
        # keep internal queue?
        # return await client.send(request)
        # TODO move to func/class
        self.active_requests += 1

        # TODO use `print/toString` function
        print(
            f'Node {self.id} | start | request {request.id} | active {self.active_requests}')

        self.emit(Node.Event.ActiveRequestsChanged)

        resp = None
        sleep = 0
        try:
            # XXX testing only
            if DISABLE_NODE_REQUESTS:
                sleep = random.randrange(0, 3 + self.active_requests)
                await asyncio.sleep(sleep)
            else:
                resp = await self.execute_request(request.request)
        # TODO more specific error: timeout, can't connect
        except Exception as e:
            logger.error(
                f'Node#execute_request|node_id:{self.id}|req_id:{request.id}', e)
            # TODO NodeResponse error
            return {'error': e}
        finally:
            print(f'Node {self.id} finished request {request.id}')
            self.active_requests -= 1
            self.emit(Node.Event.ActiveRequestsChanged)

            return NodeResponse(self.id, resp)  # {'sleep': sleep})

    # TODO add variables
    async def execute_request(self, request):
        async with httpx.AsyncClient() as client:
            method = request.method
            url = 'http://' + ''.join([self.uri, request.scope['path']])
            # TODO add more params
            return await client.request(method, url)

    # TODO

    async def health_check():
        pass

    def __str__(self):
        return f'Node {self.id} ( {self.active_requests} )'

    # XXX no, Node shouldn't know about priority ; it should be an user's responsibility
    # e.g. NodeWrapper
    def __lt__(self, other):
        return self.active_requests < other.active_requests


# TODO in config / env vars
NODES_LIST: list[Node] = [
    Node(1, 'localhost:3001'),
    Node(2, 'localhost:3002'),
    Node(3, 'localhost:3003'),
]


class Singleton:
    __instance = None

    @classmethod
    def instance(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

# Manages the priority of nodes / balances nodes load
# ?Follow-ups on node freeze?
# NodesLoadBalancer #get_least_busy_node #rebalance
# TODO BalanceStrategy - least connections, round robin


class NodesLoadTracker(Singleton):
    # Keep a sorted heap
    _nodes_pool: list[Node]

    def __init__(self, nodes: list[Node] = NODES_LIST):
        self._nodes_pool = nodes
        self._attach_node_load_listener()

    def get_least_busy_node(self) -> Node:
        return self._nodes_pool[0]

    # protected

    # TODO speed up - rebalance(node) & move the node up or down in a tree/heap;
    # heapify would be O(n)
    def _rebalance_nodes(self, node) -> None:
        heapq.heapify(self._nodes_pool)
        # XXX

        print(f'Rebalance - {" -- ".join(self.pool_stats())}')

    def pool_stats(self):
        return map(lambda n: str(n), self._nodes_pool)

    def _attach_node_load_listener(self) -> None:
        # subscribe
        for node in self._nodes_pool:
            node.on(Node.Event.ActiveRequestsChanged, self._rebalance_nodes)


class RequestBroker(Singleton):
    def __init__(self, nodes_load_tracker: NodesLoadTracker = NodesLoadTracker.instance()):
        self._nodes_load_tracker = nodes_load_tracker

    # TODO keep some requests queue/list/set/tree?
    async def process_request(self, request: BrokerRequest) -> Response:
        try:
            node = self._nodes_load_tracker.get_least_busy_node()
            resp = await node.process_request(request)
        except Exception as e:
            # TODO route to different worker
            # XXX
            print(e)
            # TODO
            return None
        else:
            return resp


def get_request_broker():
    return RequestBroker.instance()


@router.api_route("/{full_path:path}", methods=['GET', 'POST'])
async def forward_request(
    request: Request,
    full_path: str,
    request_broker: RequestBroker = Depends(get_request_broker)
):
    # RequestParallelBroker
    resp = await request_broker.process_request(BrokerRequest(request))

    return Response(content=resp.opts.content,
                    headers=resp.opts.headers,
                    status_code=resp.opts.status_code)



@router.get('/')
async def read_root():
    return Response("Hello, it's me. A simple LoadBalancer")
