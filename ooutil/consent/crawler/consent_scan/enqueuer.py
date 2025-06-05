from rq import Retry
from tqdm import tqdm

from consent.crawler.consent_scan.kernel import kernel
from consent.util.distproc.task_enqueuer import TaskEnqueuer


async def enqueue(exper_date: str, site_urls, consent, proxy_urls, location, overwrite: bool, local_run: bool):
    q = TaskEnqueuer.get_queue()
    # Timeout: at least 4min because need to try 4 homepage URLs.
    job_timeout = 360

    assert len(site_urls) == len(proxy_urls), "site_urls and proxy_urls must have the same length."
    for (site, url), proxy_url in tqdm(zip(site_urls, proxy_urls), total=len(site_urls)):
        kwargs = {'exper_date': exper_date, 'site': site, 'url': url, 'consent': consent,
                  'proxy_url': proxy_url, 'location': location, 'overwrite': overwrite}

        if local_run:
            await kernel(**kwargs)
        else:
            q.enqueue(kernel, kwargs=kwargs, retry=Retry(max=3, interval=[30, 60, 90]), job_timeout=job_timeout)
