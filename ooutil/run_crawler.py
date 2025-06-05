import asyncio
import datetime

from consent.crawler.consent_scan.kernel import kernel


if __name__ == '__main__':
    SITE_TO_URLS = {
        # Website with no cookie management platform (CMP).
        'wikipedia.org': 'https://www.wikipedia.org/',
        # Website with no OneTrust.
        'acm.org': 'https://www.acm.org/',
        # Website with no Cookiebot.
        'brevo.com': 'https://www.brevo.com/'
    }
    EXPERIMENT_DATE = str(datetime.date.today())
    for site, url in SITE_TO_URLS.items():
        # Test crawling the sites while denying consent on them. Overwrite the output directory. Do not use any proxy.
        asyncio.run(kernel(exper_date=EXPERIMENT_DATE, site=site, url=url, consent=False, overwrite=True, proxy_url=None, location="us"))