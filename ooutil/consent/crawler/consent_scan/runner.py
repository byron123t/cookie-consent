import asyncio

import pandas as pd

from consent.crawler.consent_scan.enqueuer import enqueue
from consent.crawler.crawl_proxy import CrawlProxy
from consent.data.database.exper_result_database import ExperResultDatabase
from consent.data.top_site import TOP_SITE_MAP


PAGE_COLL_PREFIX = 'en_suc_'

def get_coll_name(site_suffix):
    """Get name of a collection."""
    return PAGE_COLL_PREFIX + site_suffix

def get_site_urls(cur_set: str, sel_sites=None):
    assert cur_set in TOP_SITE_MAP, f'{cur_set=} should be in {TOP_SITE_MAP=}'
    record_date = '2023-04-08'
    suc_sites_list = [ExperResultDatabase(record_date, get_coll_name(cur_set)).query_to_df()]
    suc_sites = pd.concat(suc_sites_list)
    if sel_sites:
        suc_sites = suc_sites[suc_sites.site.isin(sel_sites)]
    return suc_sites.to_records(index=False).tolist()

def validate_site_urls(site_urls):
    sites = [site_url[0] for site_url in site_urls]
    site_counts = pd.Series(sites).value_counts()
    dup_sites = site_counts[site_counts > 1]
    assert len(dup_sites) == 0, f'There are duplicate sites:\n{dup_sites.to_dict()}'

LOCATION_TO_EXPER_DATE = {'ca': '2023-04-10', 'de': '2023-04-14', 'uk': '2023-04-24'}

async def main():
    consent = False
    location = 'ca'
    exper_date = LOCATION_TO_EXPER_DATE[location]
    cur_set =  '20k_100k'

    sel_sites = None
    site_urls = get_site_urls(cur_set, sel_sites)

    if len(site_urls) == 0: print("Nothing to scan"); return

    proxy_urls = [CrawlProxy.get_proxy_url_ip(location) for _ in range(len(site_urls))]

    overwrite = True if sel_sites is not None else False
    print(f'Num sites to scan: {len(site_urls):,d}\n{site_urls[:10]=}')

    validate_site_urls(site_urls)
    await enqueue(exper_date, site_urls, consent, proxy_urls, location, overwrite=overwrite, local_run=True)


if __name__ == '__main__':
    asyncio.run(main())
