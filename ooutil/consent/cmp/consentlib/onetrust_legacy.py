from consent.cmp.consentlib.consent_lib import ConsentLib

class OneTrustLegacyConsentLib(ConsentLib):
    name = 'onetrust_legacy'
    pref_save_btn_sels = ['button.save-preference-btn-handler']
    pref_menu_sels = ['#optanon-popup-wrapper']
