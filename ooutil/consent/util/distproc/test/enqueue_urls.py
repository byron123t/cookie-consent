"""Enqueue urls to process."""

import time

from redis import Redis
from rq import Queue

from task import process_url
from redis_conf import REDIS_URL


redis_conn = Redis.from_url(REDIS_URL)


def enqueue():
    q = Queue('low', connection=redis_conn)
    jobs = []
    for url in ['https://google.com', 'https://nytimes.com']:
        j = q.enqueue(process_url, url)
        jobs.append(j)

    print('Wait for jobs to finish')
    for j in jobs:
        while j.get_status() != 'finished':
            time.sleep(.5)
            pass

        print(f"Status: {j.get_status()}")
        print(f"Result: {j.result}")


if __name__ == '__main__':
    enqueue()
