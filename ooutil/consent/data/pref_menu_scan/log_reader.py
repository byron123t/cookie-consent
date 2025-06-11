# %%
"""Manage site prefs in pref menu scan."""

from pathlib import Path
import json
from typing import List
from multiprocessing import Pool

import pandas as pd
from src.ooutil.df_util import expand_dict_col


def read_log(site: str, log_file: Path):
    log = json.loads(log_file.read_text())
    scan_result = log['scan_result']
    cat_df = None
    error_df = None
    if log['error'] is None:
        cat_df = pd.DataFrame(list(scan_result['category_consent'].values()))
        cat_df['pref_menu_type'] = scan_result.get('pref_menu_type')
    else:
        error_df = pd.DataFrame({'error': [log['error']]})

    for df in [cat_df, error_df]:
        if df is not None:
            df['consent_lib_name'] = scan_result.get('consent_lib_name', None)
            df['site'] = site

    warnings = pd.DataFrame({'warnings': log['warnings']})
    return cat_df, error_df, warnings


def read_log_in_dir(site_dir: Path, verbose=2):
    log_file = site_dir / 'log.json'
    if not log_file.exists():
        # raise ValueError(f'{log_file} not exists.')
        print(f'{log_file} not exists.')
        return None, None, None

    try:
        return read_log(site_dir.name, log_file)
    except Exception as e:
        print(f"Error reading {log_file}:", e)
    return None, None, None
    # prefs_data.append(aprefs)
    # warnings_data.append(awarnings)

    # prefs = pd.concat(prefs_data)
    # warnings = pd.concat(warnings_data)

    # # assert 'error' in prefs.columns, f'{prefs=}'
    # # error_mask = prefs.error.isna()
    # # errors = prefs[~error_mask][['site', 'error', 'consent_lib_name']]
    # # errors = expand_dict_col(errors, 'error')
    # # prefs = prefs[error_mask]
    # # cols_to_drop = ['error']
    # # if 'cookie_decl' in prefs.columns:
    # #     cols_to_drop += ['cookie_decl']
    # # prefs = prefs.drop(columns=cols_to_drop)

    # return prefs, errors, warnings


def read_log_in_site_dir(scan_dir_name: str, site_dir: Path):
    prefs, errors, warnings = read_log_in_dir(site_dir)
    for df in [prefs, errors, warnings]:
        if df is not None:
            assert isinstance(df, pd.DataFrame)
            df['scan'] = scan_dir_name
    return prefs, errors, warnings

def read_logs_in_scans(scan_dirs: List[Path], verbose=2):
    scan_site_dir_pairs = []
    for scan_dir in scan_dirs:
        assert scan_dir.is_dir()
        if verbose >= 2:
            print(f'Read logs in scans {scan_dir.parent.name}/{scan_dir.name}')
        for site_dir in scan_dir.glob('*/'):
            if site_dir.is_dir():
                scan_site_dir_pairs.append((scan_dir.name, site_dir))

    pool = Pool(32)
    results = pool.starmap(read_log_in_site_dir, scan_site_dir_pairs)

    prefs_dfs = []; errors_dfs = []; warnings_dfs = []
    for prefs, errors, warnings in results:
        if prefs is not None:
            prefs_dfs.append(prefs)
        if errors is not None:
            errors_dfs.append(errors)
        if warnings is not None:
            warnings_dfs.append(warnings)
    prefs_df = pd.concat(prefs_dfs)
    errors_df = pd.concat(errors_dfs)
    warnings_df = pd.concat(warnings_dfs)
    # assert not prefs_df.drop(columns=['cookie_decl']).duplicated().any(), "Category preferences contain duplicates"

    return prefs_df, errors_df, warnings_df

if __name__ == '__main__':
    # test()
    pass
    # %%
    from consent.consistency.util import _CA_SCAN_DIRS
    prefs, errors, warnings = read_logs_in_scans(_CA_SCAN_DIRS)

    # %%
    prefs.head()
    # %%
    assert not prefs.drop(columns=['cookie_decl']).duplicated().any()
    # %%
    prefs[['site', 'consent_lib_name']].drop_duplicates().consent_lib_name.value_counts()
    # %%
    errors.consent_lib_name.value_counts()

    # %%
    warnings['num_warnings'] = warnings.warnings.map(len)
    warnings.num_warnings.value_counts()
    # %%
    warnings.sort_values(by='num_warnings', ascending=False, inplace=True)
# %%
    warnings.iloc[0].warnings


# %%
