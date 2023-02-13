import httpx
import asyncio


urls_get_url = 'http://localhost:8000/urls'

async def request(client, url):
    response = await client.get(url)
    return response.text


def test_suite_1(client):
    return [request(client, url) for url in [urls_get_url] * 7]


async def run():
    print('--- Start load tests ---')
    async with httpx.AsyncClient() as client:
        tasks = test_suite_1(client)

        print(f"Waiting on test suite {len(tasks)}")
        result = await asyncio.gather(*tasks)
        print(result)


if __name__ == "__main__":
    asyncio.run(run())
