from consent.cmp.consentlib.consent_lib import ConsentLib


class TrustArcConsentLib(ConsentLib):
    name = 'trustarc'
    pref_menu_sels = ['iframe[src^="https://consent-pref.trustarc.com/"]', '#trustarcNoticeFrame']
