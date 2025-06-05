"""Enqueue home-page-load tasks."""

from typing import List
from rq import Retry
from tqdm import tqdm

from consent.crawler.home_page_load.kernel import kernel
from consent.util.distproc.task_enqueuer import TaskEnqueuer


async def enqueue(websites, exper_date, proxy_urls: List[str], location: str, is_async=True, local_run=False):
    """Run kernel with each website and save to collection."""
    assert isinstance(websites, list)
    q = TaskEnqueuer.get_queue()

    assert len(websites) == len(proxy_urls), "site_urls and proxy_urls must have the same length."
    for website, proxy_url in tqdm(zip(websites, proxy_urls), total=len(websites)):
        kwargs = {'website': website, 'exper_date': exper_date, 'proxy_url': proxy_url, 'location': location}
        job_timeout = 360 # Timeout: at least 4min because need to try 4 homepage URLs.

        if local_run:
            await kernel(**kwargs)
        else:
            q.enqueue(kernel, kwargs=kwargs, retry=Retry(
                max=3, interval=[30, 60, 90]), is_async=is_async, job_timeout=job_timeout)
