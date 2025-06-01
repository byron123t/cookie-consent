from typing import List, Optional, Type

from consent.cmp.consentlib.consent_lib import ConsentLib, ConsentCookie
from consent.cmp.consentlib.cookiebot import CookiebotLegacyConsentLib, CookiebotConsentLib, CookiebotNewConsentLib
from consent.cmp.consentlib.onetrust import OneTrustConsentLib
from consent.cmp.consentlib.onetrust_legacy import OneTrustLegacyConsentLib
from consent.cmp.consentlib.trustarc import TrustArcConsentLib
from consent.cmp.consentlib.termly import TermlyConsentLib

consent_lib_classes: List[Type[ConsentLib]] = [
    CookiebotLegacyConsentLib, CookiebotNewConsentLib, OneTrustConsentLib, OneTrustLegacyConsentLib, TermlyConsentLib, TrustArcConsentLib]


class ConsentLibFactory:
    @classmethod
    def get_consent_cookie_class_by_name(cls, consent_lib_name, verbose=0) -> Type[ConsentCookie]:
        if verbose >= 2: print(f'get_consent_cookie_class_by_name {consent_lib_name=}')
        for consent_lib_class in consent_lib_classes:
            if consent_lib_class.name == consent_lib_name:
                return consent_lib_class.consent_cookie_cls
        raise NotImplementedError(f"{consent_lib_name} not supported")
