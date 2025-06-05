"""Set up and enqueue the kernel."""

import asyncio
import random

from consent.crawler.home_page_load.enqueuer import enqueue
from consent.crawler.crawl_proxy import CrawlProxy
from consent.data.database import exper_result_database
from consent.data.database.exper_result_database import ExperResultDatabase, ExperResultRegistry
from consent.data.top_site import TopSite
from ooutil.stealth.stealth_mode import STEALTH_MODE_TEST_URL

def get_websites(n: int, exper_date: str, sample_m=0, exclude_done_sites=False, verbose=2):
    top_n_sites = TopSite.get_site_df(limit=n)

    if exclude_done_sites:
        done_db = ExperResultDatabase(exper_date, 'home_page_load_result')
        done_sites = [] if not done_db.exists() else done_db.query_to_df(projection=['site']).site.to_list()
        if verbose >= 2:
            if verbose >= 3: print(f'{done_sites=}')
            print(f'Before excluding {len(top_n_sites)=}')
        top_n_sites = top_n_sites[~top_n_sites.site.isin(done_sites)]
        if verbose >= 2:
            print(f'After excluding {len(top_n_sites)=}')

    if sample_m > 0:
        assert sample_m <= n, f'sample should not be larger than n {sample_m=} {n=}'
        top_n_sites = top_n_sites.sample(sample_m)

    return top_n_sites.site.tolist()


async def main():
    exper_date = '2023-04-08'

    websites = get_websites(200000, exper_date, sample_m=0, exclude_done_sites=True) # 0)  # 50)

    print(f'To crawl {len(websites):,d} sites')
    print(f"First sites: {websites[:10]}")
    print(f"Last sites: {websites[-10:]}")

    location = 'eu'
    proxy_urls = [CrawlProxy.get_proxy_url_ip(location) for _ in range(len(websites))]

    random.shuffle(websites)
    await enqueue(websites, exper_date, proxy_urls, location=location, local_run=True)


if __name__ == '__main__':
    asyncio.run(main())
