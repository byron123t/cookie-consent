from typing import List, Optional, Type
from urllib.parse import urlparse

from consent.cmp.consentlib.consent_resource.resource import ConsentResource
from consent.cmp.consentlib.consent_resource.onetrust import EnJsonOneTrustResource, ConsentJsOneTrustResource
from consent.cmp.consentlib.consent_resource.cookiebot import CcJsCookiebotResource
from consent.cmp.consentlib.consent_resource.termly import TermlyCookiesResource


class ConsentResourceFactory:
    sub_classes: List[Type[ConsentResource]] = [EnJsonOneTrustResource, ConsentJsOneTrustResource, CcJsCookiebotResource, TermlyCookiesResource]

    @classmethod
    def get_class_from_url(cls, cur_url: str, url: str, verbose=0) -> Optional[Type[ConsentResource]]:
        """Match URL with subclasses."""
        try:
            url_parts = urlparse(url)
            for subclass in cls.sub_classes:
                if subclass.match_url(cur_url, url_parts):
                    return subclass
        except Exception as e:
            if verbose >= 2: print(f"Error matching url: {cur_url=} {url=}:", e)
        return None

    @classmethod
    def get_class(cls, lib_name: str, pattern_name: str) -> Optional[Type[ConsentResource]]:
        for subclass in cls.sub_classes:
            if subclass.lib_name == lib_name and subclass.pattern_name == pattern_name:
                return subclass
        return None
