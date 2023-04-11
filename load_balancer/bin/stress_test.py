import httpx
import asyncio
import timeit


urls_get_url = 'http://localhost:8000/urls'
test_suite_1_times = [ 1, 1, 1, 1, 1 ]
test_suite_1_config = zip(test_suite_1_times, [urls_get_url] * len(test_suite_1_times))


async def sleepy_request(client: httpx.AsyncClient, url, sleep):
    response = await client.get(url, headers={'x-fake-processing-time': str(sleep)})
    et = response.headers.get('x-process-time')
    worker_id = response.headers.get('x-worker-id')
    return f'id:{worker_id}-et:{et}'


def test_suite_1(client):
    return [sleepy_request(client, url, sleep) for sleep, url in test_suite_1_config]

def async_benchmark(func):
    async def wrapper():
        start = timeit.default_timer()
        await func()
        print(f"Benchmark: {timeit.default_timer()-start}")
 
    return wrapper

# TODO benchmark
@async_benchmark
async def run():
    print('--- Start load tests ---')
    async with httpx.AsyncClient() as client:
        tasks = test_suite_1(client)

        print(f"Waiting on test suite {len(tasks)}")
        result = await asyncio.gather(*tasks)
        print(result)


if __name__ == "__main__":
    asyncio.run(run())
