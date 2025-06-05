from pathlib import Path
from functools import lru_cache
from titlecase import titlecase

from consent.util.default_path import get_data_dir2


LOCATION_TO_EXPER_DATE = {
    'capetown': '2024-10-12',
    'ireland': '2024-10-11',
    'london': '2024-10-06',
    'mi': '2024-10-04',
    'singapore': '2024-10-08',
    'sydney': '2024-10-07',
    'toronto': '2024-10-09',
    'sf': '2024-10-10',
}
    # 'aus': '2023-11-27',
    # 'ca': '2023-11-22',
    # 'can': '2023-11-23',
    # 'ie': '2023-11-21',
    # 'sg': '2023-11-26',
    # 'uk': '2023-11-28',
    # 'za': '2023-11-25'
LOCATIONS = sorted(list(LOCATION_TO_EXPER_DATE.keys()))

def get_data_dir2_by_location(location):
    return get_data_dir2(LOCATION_TO_EXPER_DATE[location])

_LOCATION_TO_ROOT_DIR = {
    loc: get_data_dir2_by_location(loc)
        for loc in LOCATION_TO_EXPER_DATE.keys()
}

_LOCATION_TO_SCAN_DIRS = {
    loc: [_LOCATION_TO_ROOT_DIR[loc] / 'pref_menu_scan_0k_20k']
        for loc in LOCATION_TO_EXPER_DATE.keys()
}

def get_scan_root_dir(location):
    root_dir = _LOCATION_TO_ROOT_DIR[location]
    assert root_dir.exists()
    return root_dir

def get_scan_dirs(location):
    scan_dirs = _LOCATION_TO_SCAN_DIRS[location]
    assert all(scan_dir.exists() for scan_dir in scan_dirs)
    return scan_dirs

FIG_DIR = Path.home() / 'cookie-tables/data/plots'
assert FIG_DIR.exists() and FIG_DIR.is_dir()

@lru_cache(maxsize=None)
def normalize_cookie_category_name(name: str, verbose=0):
    name = name.lower().strip()
    name = name.replace('personal information', 'personal data')
    for remove_kw in ['personalize', 'strictly', 'extend', 'measure']:
        name = name.replace(remove_kw, '')

    for kw in ['targeting', 'ads', 'advertising', 'marketing']:
        if kw in name:
            name = 'targeting'

    name = name.replace('targeting', 'advertising')

    parts = name.split()
    if 'manage' in name:
        if verbose >= 2: print(parts)
    if len(parts) > 3 and parts[-3] == '/' and parts[-2] == 'manage' and parts[-1] == 'cookies':
        parts = parts[:-3]

    if len(parts) > 2 and parts[-2] == 'website' and parts[-1] == 'cookies':
        parts = parts[:-2]

    if parts[-1] in ['cookies', 'cookie']:
        del parts[-1]

    result = ' '.join(parts)

    if result in ['necessary', 'required', 'essential']:
        result = 'necessary'

    return titlecase(result)


def test():
    print(normalize_cookie_category_name("necessary cookies"))


if __name__ == '__main__':
    test()
    print("Tests passed.")
