"""Manage cookies."""

from typing import Dict, List

import pandas as pd

from ooutil.cookie_util import url_domain_match


class CookieStore:
    """Manage cookies of a browser context."""

    def __init__(self, cookies: List[Dict], page_url):
        self.df = pd.DataFrame(cookies)
        self.page_url = page_url

    def find_cookies_in_page(self, cookie_name: str) -> pd.DataFrame:
        cookies = self.df
        found = cookies[(cookies.name == cookie_name) & cookies.domain.map(
            lambda domain: url_domain_match(self.page_url, domain))]

        return found

    # def find_cookies_by_domain(self, cookie_name: str, domain: str, verbose=0) -> pd.DataFrame:
    #     if verbose >= 2: print(f"find_cookies_by_domain {cookie_name=} {domain=}")
    #     cookies = self.df
    #     found = cookies[(cookies.name == cookie_name) & cookies.domain.map(
    #         lambda adomain: adomain.endswith(domain))]

    #     return found