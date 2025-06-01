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
        if verbose >= 3: print(f"get_class_from_url: cur_url {cur_url}, url {url}")
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


def test_path_patterns():
    cur_url = 'https://www.discoveryplus.com/'
    url = 'https://cdn.cookielaw.org/consent/355b7913-7ddc-4533-a80b-cab1202ded33/0191db59-87a8-79f9-a4ab-5eaa7368104b/en.json'
    consent_lib = ConsentResourceFactory.get_class_from_url(cur_url, url)
    assert consent_lib.lib_name == 'onetrust' and consent_lib.pattern_name == 'en.json'

    url = 'https://cdn.cookielaw.org/consent/6c9e9ec6-e434-4a0b-919e-c10a033acd76.js'
    consent_lib = ConsentResourceFactory.get_class_from_url(cur_url, url)
    assert consent_lib.lib_name == 'onetrust' and consent_lib.pattern_name == 'consent_js'

    url = 'https://cdn.cookielaw.org/consent/fc3cc7e3-d552-4387-a432-96bccfa03f08/96effdc8-d15f-46bb-88c2-8b2c9e3cf8a1/en.json'
    consent_lib = ConsentResourceFactory.get_class_from_url(cur_url, url)
    assert consent_lib.lib_name == 'onetrust' and consent_lib.pattern_name == 'en.json'

    url = 'https://consent.cookiebot.com/54bd0412-5733-43e7-9dda-b3f1cecce603/cc.js?renew=false&referer=www.fully-kiosk.com&dnt=false&forceshow=false&cbid=54bd0412-5733-43e7-9dda-b3f1cecce603&brandid=Cookiebot&framework='
    consent_lib = ConsentResourceFactory.get_class_from_url(cur_url, url)
    assert consent_lib.lib_name == 'cookiebot' and consent_lib.pattern_name == 'cc.js'

    url = 'https://consent.cookiebot.com/b9c70e75-4958-46f9-9410-6f8e5a3fca4c/cc.js?renew=false&referer=10fastfingers.com&dnt=false&forceshow=false&cbid=b9c70e75-4958-46f9-9410-6f8e5a3fca4c&brandid=Cookiebot&framework=IABv2'
    consent_lib = ConsentResourceFactory.get_class_from_url(cur_url, url)
    assert consent_lib.lib_name == 'cookiebot' and consent_lib.pattern_name == 'cc.js'


if __name__ == '__main__':
    test_path_patterns()
    print('Tests passed.')
