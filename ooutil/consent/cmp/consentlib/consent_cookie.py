from typing import Dict

import pandas as pd


CONSENT_COOKIE_DECODE_ERROR = 'consent_cookie_decode_error'


class ConsentCookie:
    """Represent a consent-preference cookie."""
    consent_cookie_name = ''
    local_storage_key = ''

    def __init__(self, cookie: Dict[str, str]):
        self._cookie = cookie

    @property
    def domain(self):
        return self._cookie['domain']

    @property
    def cookie(self):
        return self._cookie

    def get_characteristic_val(self):
        # Used to distinguish multiple consent cookies.
        raise NotImplementedError

    def get_cat_to_pref(self) -> Dict[str, str]:
        raise NotImplementedError

    def get_cat_prefs(self) -> pd.DataFrame:
        group_consent = self.get_cat_to_pref()
        return pd.DataFrame(group_consent.items(), columns=['category_id', 'consent'])
