import heapq
import httpx
import asyncio
import random

import logging

from typing import Literal
from fastapi import APIRouter, Depends, Response, Request, status
# from pydantic import BaseModel, HttpUrl, Field

logger = logging.getLogger('routes')
logging.basicConfig(format="%(threadName)s:%(levelname)s:%(message)s", level=logging.DEBUG)

router = APIRouter()


DISABLE_WORKER_REQUESTS = True


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


class WorkerResponse:
    def __init__(self, worker_id: int, options: dict):
        self.worker_id = worker_id
        self.response = options

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
        # TODO asyncio.create_task (make async)
        if event not in self._subscribers:
            return

        for sub_callback in self._subscribers[event]:
            # notify with Worker
            sub_callback(self)

class Comparable:
    _comparator: callable

    def set_comparator(self, comparator: callable):
        self._comparator = comparator

    def __lt__(self, other):
        return self._comparator(self, other)

# XXX use
class WorkerTimeout(Exception):
    pass


# TODO rename: Worker/WorkerWorker/ServiceWorker/
class Worker(Emitter, Comparable):
    class Event:
        StateChanged = 'state_changed'

    id: int
    uri: str
    active_requests: int = 0

    def __init__(self, _id, _uri):
        super().__init__()

        self.id = _id
        self.uri = _uri

    def increase_active_requests(self):
        self.active_requests += 1
        # TODO asyncio.create_task
        self.emit(Worker.Event.StateChanged)

    def decrease_active_requests(self):
        self.active_requests -= 1
        # TODO asyncio.create_task
        # TODO decorate?
        self.emit(Worker.Event.StateChanged)

    async def process_request(self, request: BrokerRequest) -> WorkerResponse:
        self.increase_active_requests()

        logger.info(f'Worker {self.id} | start | request {request.id} | active {self.active_requests}')

        resp: Response = None
        try:
            resp = await self.execute_request(request.request)
        # TODO more specific error: timeout, can't connect
        except Exception as e:
            logger.error(
                f'Worker#execute_request|worker_id:{self.id}|req_id:{request.id}|Error: {e}')

            # TODO - "Anti corruption": translate to internal exception
            raise e
        else:
            logger.info(f'Worker {self.id} | end | request {request.id} | ET {resp.headers.get("x-process-time")} | active {self.active_requests}')

            # TODO update_metrics(request) | 
            # if req => +1 active
            # else => -1 active ; add process time ; ...
            self.decrease_active_requests()

            return WorkerResponse(self.id, resp)

    # TODO add variables
    async def execute_request(self, request):
        # XXX testing only
        if DISABLE_WORKER_REQUESTS:
            # TODO return as response with "execution time"
            sleep = random.randrange(0, 3 + self.active_requests)
            await asyncio.sleep(sleep)
            return httpx.Response(status_code=200, headers={'X-Process-Time': str(sleep), 'X-Worker-Id': str(self.id)})
        else:
            async with httpx.AsyncClient() as client:
                method = request.method
                url = 'http://' + ''.join([self.uri, request.scope['path']])
                # TODO add more params
                return await client.request(method, url)

    async def health_check():
        pass

    def __str__(self):
        return f'Worker {self.id} ( {self.active_requests} )'

    # XXX no, Worker shouldn't know about priority ; it should be an user's responsibility
    # e.g. WorkerWrapper
    def __lt__(self, other):
        return self.active_requests < other.active_requests


# TODO in config / env vars
WORKERS_LIST: list[Worker] = [
    Worker(1, 'localhost:3001'),
    Worker(2, 'localhost:3002'),
    Worker(3, 'localhost:3003'),
]


class Singleton:
    __instance = None

    @classmethod
    def instance(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = cls(*args, **kwargs)
        return cls.__instance

# Manages the priority of workers / balances workers load
# ?Follow-ups on worker freeze?
# WorkersLoadBalancer #get_worker #rebalance
# TODO BalanceStrategy - least connections, round robin


class BalancedWorkerPool(Singleton):
    # Keep a sorted heap
    _worker_pool: list[Worker]

    def __init__(self, workers: list[Worker] = WORKERS_LIST):
        self._worker_pool = workers
        # TODO make sense
        self._setup_pool()

    async def process_request(self, request) -> WorkerResponse:
        worker = self.get_worker()
        return await worker.process_request(request)

    def get_worker(self) -> Worker:
        pass

    def pool_stats(self):
        return map(lambda n: str(n), self._worker_pool)

    # protected

    def _setup_pool(self):
        pass

    def _worker_pool(self):
        return self._worker_pool

from abc import ABC, abstractmethod


# Factory?
class RoundRobinWorkerPool(BalancedWorkerPool):
    current_worker_idx: int = 0

    def get_worker(self):
        self.current_worker_idx = (self.current_worker_idx + 1) % len(self._worker_pool)
        return self._worker_pool[self.current_worker_idx]


class WorkerComparators:
    ACTIVE_REQUESTS_COMPARATOR = lambda self, other : self.active_requests < other.active_requests

# Uses different comparators: ActiveRequestWorkerPool; RequestElapseTimeWorkerPool
class MetricBasedWorkerPool(BalancedWorkerPool):
    def __init__(self):
        super().__init__()
        self._attach_worker_load_listener()

    def get_worker(self):
        return self._worker_pool[0]

    # TODO speed up - rebalance(worker) & move the worker up or down in a tree/heap;
    # heapify would be O(n)
    def _rebalance_workers(self, worker=None) -> None:
        heapq.heapify(self._worker_pool)

        logger.info(f'Rebalance {worker.id if worker else ""} - {" -- ".join(self.pool_stats())}')

    def set_comparator(self, comparator):
        # TODO rework ; Workaround to use the `heapq.heapify` out of the box
        for worker in self._worker_pool:
            worker.set_comparator(comparator)


    def _setup_pool(self):
        # TODO Decorate objects
        # - Attach health watch listeners
        # - Enhance workers - comparator
        self._rebalance_workers()

    def _attach_worker_load_listener(self) -> None:
        # subscribe
        for worker in self._worker_pool:
            worker.on(Worker.Event.StateChanged, self._rebalance_workers)

class BalanceStrategy:
    ROUND_ROBIN = 'round_robin'
    LEAST_ACTIVE_REQUESTS = 'least_active_requests'

# TODO like ExecutorService - java
worker_config = [{'id': 1, 'uri': 'localhost:3001'}]
class LoadBalancer(Singleton):
    # TODO pass worker pool directly?
    def __init__(self, balance_strategy = BalanceStrategy.ROUND_ROBIN):
        # TODO should loadbalancer know about config?
        # self.worker_pool = BalancedWorkerPool(worker_config)
        self._build_pool(balance_strategy)

    def _build_pool(self, strategy):
        pool_cls = None
        # TODO simplify factory
        if strategy == BalanceStrategy.ROUND_ROBIN:
            pool = RoundRobinWorkerPool()
        elif strategy == BalanceStrategy.LEAST_ACTIVE_REQUESTS:
            pool = MetricBasedWorkerPool()
            pool.set_comparator(WorkerComparators.ACTIVE_REQUESTS_COMPARATOR)

        self.worker_pool = pool

    # TODO keep some requests queue/list/set/tree?
    async def process_request(self, request: BrokerRequest) -> Response:
        try:
            resp = await self.worker_pool.process_request(request)
        except Exception as e:
            # - quarantine
            # - reset metrics
            # TODO route to different worker
            # XXX
            # logger.error(e)
            raise e
            # TODO
            return None
        else:
            return resp


def get_load_balancer():
    # TODO split in two? create balancer (singleton) ; balancer.set_strategy()
    return LoadBalancer.instance(balance_strategy=BalanceStrategy.LEAST_ACTIVE_REQUESTS)


@router.api_route("/{full_path:path}", methods=['GET', 'POST'])
async def forward_request(
    request: Request,
    full_path: str,
    load_balancer: LoadBalancer = Depends(get_load_balancer)
):
    # RequestParallelBroker
    resp: WorkerResponse | None = await load_balancer.process_request(BrokerRequest(request))

    return Response(content=resp.response.content,
                    headers=resp.response.headers,
                    status_code=resp.response.status_code)



@router.get('/')
async def read_root():
    return Response("Hello, it's me. A simple LoadBalancer")
