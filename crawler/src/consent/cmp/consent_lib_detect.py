import json


from consent.util.default_path import get_data_dir
from consent.cmp.experimental_consent_lib_detect import detect_consent_lib_on_soup


com_rule_file = get_data_dir('2021-07-29') / \
    'Consent-O-Matic-master' / 'Rules.json'
com_rules = json.loads(com_rule_file.read_text())


def get_matchers(detectors):
    for detector in detectors:
        for detect_type, detect_val in detector.items():
            if detect_type in ['presentMatcher', 'showingMatcher']:
                yield detect_val
            assert detect_val['type'] == 'css', f"Found non-css type: detect_val['type']"


cmp_to_matchers = {}
for cmp_name, rules in com_rules.items():
    if cmp_name in ['Autodesk', 'lemonde.fr', 'dr.dk', 'ikeaToast', 'springer', 'theGuardian', 'umf.dk', 'SFR']:
        continue
    cmp_to_matchers[cmp_name] = list(get_matchers(rules['detectors']))


def detect_matchers(soup, matchers):
    for detect_val in matchers:
        target = detect_val['target']
        selector = target['selector']
        text_filters = target.get('textFilter')
        found = soup.select_one(selector)
        if found is not None:
            if text_filters is not None:
                for text_filter in text_filters:
                    if found.text.strip() == text_filter:
                        return found
            else:
                return found


def detect_cmp_com(soup):
    for cmp_name, matchers in cmp_to_matchers.items():
        found = detect_matchers(soup, matchers)
        if found is not None:
            return cmp_name
    return None

autoconsent_map = {
    'privacymgmt': ['https://cdn.privacy-mgmt.com/'],
    'tagcommander': ['http://cdn.tagcommander.com/privacy', 'https://cdn.tagcommander.com/privacy', 'https://cdn.trustcommander.net/privacy', 'https://analytics.ovh.com/ovh/privacy'],
    'trustarc': ['https://consent-pref.trustarc.com/?']
}

def detect_cmp_autoconsent(soup, frame_url):
    for cmp_name, urls in autoconsent_map.items():
        for url in urls:
            if frame_url.startswith(url):
                return cmp_name
    return None


def detect_cmp(soup, frame_url):
    """Return name of detected CMP."""
    for cmp_name in [detect_cmp_com(soup), detect_cmp_autoconsent(soup, frame_url), detect_consent_lib_on_soup(soup)]:
        if cmp_name is not None:
            return cmp_name
    return None


def get_selectors(prefix):
    selectors = set()
    for matchers in cmp_to_matchers.values():
        for matcher in matchers:
            for selector in matcher['target']['selector'].split(','):
                selector = selector.strip()
                if selector.startswith(prefix):
                    selector = selector[1:]
                    selectors.add(selector)

    return selectors

def print_selectors(prefix=''):
    selectors = get_selectors(prefix)
    print(f'{prefix=}')
    print(sorted(list(selectors)))

def print_matchers():
    print_selectors('#')
    print_selectors('.')

if __name__ == '__main__':
    print_matchers()
