import os, json, re
from tqdm import tqdm


LOCATION_TO_EXPER_DATE = {
    'za': '2024-10-12',
    'eu': '2024-10-11',
    'uk': '2024-10-06',
    'us': '2024-10-04',
    'sg': '2024-10-08',
    'au': '2024-10-07',
    'can': '2024-10-09',
    'ca': '2024-10-10',
    '2024-10-12': 'za',
    '2024-10-11': 'eu',
    '2024-10-06': 'uk',
    '2024-10-04': 'us',
    '2024-10-08': 'sg',
    '2024-10-07': 'au',
    '2024-10-09': 'can',
    '2024-10-10': 'ca',
}

preference_data = {}
cookie_data = []
for root, dirs, files in tqdm(os.walk('data/')):
    date = root.split('/')[-3]
    if 'pref_menu_scan_0k_20k_0' in root and date in LOCATION_TO_EXPER_DATE:
        for file in files:
            site = root.split('/')[-1]
            if file == 'consent_resources.json':
                with open(os.path.join(root, file), 'r') as f:
                    resources = json.load(f)
                    if LOCATION_TO_EXPER_DATE[date] not in preference_data:
                        preference_data[LOCATION_TO_EXPER_DATE[date]] = {}
                    if site not in preference_data[LOCATION_TO_EXPER_DATE[date]]:
                        preference_data[LOCATION_TO_EXPER_DATE[date]][site] = {}
                    if resources:
                        for resource in resources:
                            try:
                                data = json.loads(resource['response'])
                            except json.decoder.JSONDecodeError:
                                temp_cookies = {}
                                for line in resource['response'].split('\n'):
                                    if line.startswith('CookieConsentDialog.cookieTable'):
                                        if ' = [[' in line:
                                            category = line.split(' = [[')[0].split('CookieConsentDialog.cookieTable')[1]
                                            resources = json.loads('[[' + line.split(' = [[')[1].strip()[:-1])
                                            temp_cookies[category] = resources
                                    if line.startswith('CookieConsent.whitelist = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['whitelisted'] = json.loads(line.split('CookieConsent.whitelist = ')[1].strip()[:-1])
                                    if line.startswith('var CookiebotDialog, CookieConsentDialog; CookiebotDialog = CookieConsentDialog = new CookieControl.Dialog('):
                                        pattern = r'CookieControl\.Dialog\((.*)\);'
                                        match = re.search(pattern, line)
                                        if match:
                                            # Extract the argument list as a string
                                            arg_string = match.group(1)
                                            
                                            # Split by commas, while taking care of quoted commas within strings
                                            # This regular expression splits on commas outside of quotes
                                            args = re.findall(r"(?:'([^']*)'|[^,]+)", arg_string)

                                            # Clean up and format the arguments to handle null and boolean values as well
                                            parsed_args = [arg if arg not in ['null', 'false', 'true'] else eval(arg.capitalize()) for arg in args]
                                            preference_data[LOCATION_TO_EXPER_DATE[date]][site]['dialog'] = parsed_args
                                        else:
                                            preference_data[LOCATION_TO_EXPER_DATE[date]][site]['dialog'] = line
                                            print("No match found.")
                                    if line.startswith('CookieConsentDialog.noCookiesTypeText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['noCookiesTypeText'] = line.split('CookieConsentDialog.noCookiesTypeText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.noCookiesText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['noCookiesText'] = line.split('CookieConsentDialog.noCookiesText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookiesOverviewText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookiesOverviewText'] = line.split('CookieConsentDialog.cookiesOverviewText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.consentTitle = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['consentTitle'] = line.split('CookieConsentDialog.consentTitle = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.consentSelection = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['consentSelection'] = line.split('CookieConsentDialog.consentSelection = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.details = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['details'] = line.split('CookieConsentDialog.details = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.about = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['about'] = line.split('CookieConsentDialog.about = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.domainConsent = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['domainConsent'] = line.split('CookieConsentDialog.domainConsent = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.domainConsentList = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['domainConsentList'] = line.split('CookieConsentDialog.domainConsentList = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.providerLinkText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['providerLinkText'] = line.split('CookieConsentDialog.providerLinkText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.opensInNewWindowText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['opensInNewWindowText'] = line.split('CookieConsentDialog.opensInNewWindowText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.externalLinkIconAltText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['externalLinkIconAltText'] = line.split('CookieConsentDialog.externalLinkIconAltText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieHeaderTypeNecessary = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieHeaderTypeNecessary'] = line.split('CookieConsentDialog.cookieHeaderTypeNecessary = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieHeaderTypePreference = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieHeaderTypePreference'] = line.split('CookieConsentDialog.cookieHeaderTypePreference = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieHeaderTypeAdvertising = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieHeaderTypeAdvertising'] = line.split('CookieConsentDialog.cookieHeaderTypeAdvertising = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieHeaderTypeUnclassified = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieHeaderTypeUnclassified'] = line.split('CookieConsentDialog.cookieHeaderTypeUnclassified = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieTableHeaderName = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieTableHeaderName'] = line.split('CookieConsentDialog.cookieTableHeaderName = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieTableHeaderProvider = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieTableHeaderProvider'] = line.split('CookieConsentDialog.cookieTableHeaderProvider = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieTableHeaderPurpose = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieTableHeaderPurpose'] = line.split('CookieConsentDialog.cookieTableHeaderPurpose = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieTableHeaderType = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieTableHeaderType'] = line.split('CookieConsentDialog.cookieTableHeaderType = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.cookieTableHeaderExpiry = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['cookieTableHeaderExpiry'] = line.split('CookieConsentDialog.cookieTableHeaderExpiry = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.promotionBannerEnabled = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['promotionBannerEnabled'] = line.split('CookieConsentDialog.promotionBannerEnabled = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.bulkconsentDomainsString = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['bulkconsentDomainsString'] = line.split('CookieConsentDialog.bulkconsentDomainsString = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.domainlist = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['domainlist'] = line.split('CookieConsentDialog.domainlist = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.domainlistCount = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['domainlistCount'] = line.split('CookieConsentDialog.domainlistCount = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.bannerButtonDesign = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['bannerButtonDesign'] = line.split('CookieConsentDialog.bannerButtonDesign = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.ucDataShieldPromotionBannerTitle = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['ucDataShieldPromotionBannerTitle'] = line.split('CookieConsentDialog.ucDataShieldPromotionBannerTitle = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.ucDataShieldPromotionBannerBody = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['ucDataShieldPromotionBannerBody'] = line.split('CookieConsentDialog.ucDataShieldPromotionBannerBody = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.ucDataShieldPromotionBannerCTA = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['ucDataShieldPromotionBannerCTA'] = line.split('CookieConsentDialog.ucDataShieldPromotionBannerCTA = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.impliedConsentOnScroll = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['impliedConsentOnScroll'] = line.split('CookieConsentDialog.impliedConsentOnScroll = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.impliedConsentOnRefresh = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['impliedConsentOnRefresh'] = line.split('CookieConsentDialog.impliedConsentOnRefresh = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.showLogo = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['showLogo'] = line.split('CookieConsentDialog.showLogo = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.mandatoryText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['mandatoryText'] = line.split('CookieConsentDialog.mandatoryText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.logoAltText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['logoAltText'] = line.split('CookieConsentDialog.logoAltText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.prechecked.preferences = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['precheckedPreferences'] = line.split('CookieConsentDialog.prechecked.preferences = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.prechecked.statistics = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['precheckedStatistics'] = line.split('CookieConsentDialog.prechecked.statistics = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.prechecked.marketing = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['precheckedMarketing'] = line.split('CookieConsentDialog.prechecked.marketing = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.optionaloptinSettings.displayConsentBanner = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['displayConsentBanner'] = line.split('CookieConsentDialog.optionaloptinSettings.displayConsentBanner = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.bannerCloseButtonEnabled = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['bannerCloseButtonEnabled'] = line.split('CookieConsentDialog.bannerCloseButtonEnabled = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.background = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['background'] = line.split('CookieConsentDialog.customColors.background = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.text = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['text'] = line.split('CookieConsentDialog.customColors.text = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.highlight = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['highlight'] = line.split('CookieConsentDialog.customColors.highlight = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.shade = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['shade'] = line.split('CookieConsentDialog.customColors.shade = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.acceptBackground = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['acceptBackground'] = line.split('CookieConsentDialog.customColors.acceptBackground = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.acceptText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['acceptText'] = line.split('CookieConsentDialog.customColors.acceptText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.acceptBorder = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['acceptBorder'] = line.split('CookieConsentDialog.customColors.acceptBorder = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.selectionBackground = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['selectionBackground'] = line.split('CookieConsentDialog.customColors.selectionBackground = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.selectionText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['selectionText'] = line.split('CookieConsentDialog.customColors.selectionText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.selectionBorder = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['selectionBorder'] = line.split('CookieConsentDialog.customColors.selectionBorder = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.declineBackground = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['declineBackground'] = line.split('CookieConsentDialog.customColors.declineBackground = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.declineText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['declineText'] = line.split('CookieConsentDialog.customColors.declineText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.customColors.declineBorder = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['declineBorder'] = line.split('CookieConsentDialog.customColors.declineBorder = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.lastUpdatedText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['lastUpdatedText'] = line.split('CookieConsentDialog.lastUpdatedText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.lastUpdatedDate = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['lastUpdatedDate'] = line.split('CookieConsentDialog.lastUpdatedDate = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsent.whitelist = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['whitelist'] = line.split('CookieConsent.whitelist = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.privacyPolicies = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['privacyPolicies'] = line.split('CookieConsentDialog.privacyPolicies = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.privacyPolicyText = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['privacyPolicyText'] = line.split('CookieConsentDialog.privacyPolicyText = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.userCountry = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['userCountry'] = line.split('CookieConsentDialog.userCountry = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsent.userCountry = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['userCountry'] = line.split('CookieConsent.userCountry = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsentDialog.userCulture = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['userCulture'] = line.split('CookieConsentDialog.userCulture = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsent.consentLifetime = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['consentLifetime'] = line.split('CookieConsent.consentLifetime = ')[1].strip()[:-1]
                                    if line.startswith('CookieConsent.responseMode = '):
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site]['responseMode'] = line.split('CookieConsent.responseMode = ')[1].strip()[:-1]
                                continue
                            if 'DomainData' not in data:
                                continue
                            for key, val in data['DomainData'].items():
                                for key1 in ['pccontinueWithoutAcceptText', 'MainText', 'MainInfoText', 'AboutText', 'AboutCookiesText', 'ConfirmText', 'AllowAllText', 'CookiesUsedText', 'CookiesDescText', 'AboutLink', 'AlertNoticeText', 'AlertCloseText', 'AlertMoreInfoText', 'CookieSettingButtonText', 'AlertAllowCookiesText', 'BannerPosition', 'PreferenceCenterConfirmText', 'VendorListText', 'ThirdPartyCookieListText', 'PreferenceCenterManagePreferencesText', 'PreferenceCenterMoreInfoScreenReader', 'CookieListTitle', 'CloseShouldAcceptAllCookies', 'CookieListDescription', 'BannerCloseButtonText', 'showBannerCloseButton', 'ShowAlertNotice', 'AcceptAllCookies', 'ConsentModel', 'VendorConsentModel', 'ChoicesBanner', 'PCAccordionStyle', 'ReconsentFrequencyDays', 'BannerShowRejectAllButton']:
                                    if key == key1:
                                        preference_data[LOCATION_TO_EXPER_DATE[date]][site][key] = val
        with open('data/cmp_ui_data.json', 'w') as f:
            json.dump(preference_data, f, indent=4)
