# %%
from collections import Counter

from consent.consistency.util import _CA_SCAN_DIRS
from consent.data.pref_menu_scan.cookie_decl_reader import read_cookie_decls_in_scans

cookie_decls = read_cookie_decls_in_scans(_CA_SCAN_DIRS)
print(f"Num cookies: {len(cookie_decls):,d}, Num sites: {cookie_decls.site.nunique():,d}")
cookie_decls.head()

#%%
cb = cookie_decls[cookie_decls.lib_name == 'cookiebot']
cb.consent_mode.unique()
# %%
ot = cookie_decls[cookie_decls.lib_name == 'onetrust']
ot.consent_mode.unique()
# %%
ala_mode = 'always active'
noway_sites = []
some_ala_sites = []
one_ala_sites = []
noway_cats = []
some_ala_cats = []
one_ala_cats = []
sites_with_inact = ot[ot.consent_mode == ala_mode].site.unique()
for site in sites_with_inact:
    site_cookies = ot[(ot.site == site)]
    n_cats = site_cookies.category.nunique()
    ala_cats = site_cookies[site_cookies.consent_mode == ala_mode].category.unique().tolist()
    n_ala_cats = len(ala_cats)
    assert 0 <= n_ala_cats <= n_cats
    if (n_ala_cats == n_cats): # n_cats may be = 1
        noway_sites.append(site)
        noway_cats.extend(ala_cats)
    elif (n_ala_cats > 1):
        some_ala_sites.append(site)
        some_ala_cats.extend(ala_cats)
    else:
        one_ala_sites.append(site)
        one_ala_cats.extend(ala_cats)
# %%
assert len(set(noway_sites).intersection(set(some_ala_sites))) == 0

# %%
print(f"1 ala sites: {len(one_ala_sites)}")
print(f"total sites: {len(noway_sites + some_ala_sites + one_ala_sites)}")
print(f"No-way-to-opt-out sites: {len(noway_sites)}")
print(f"Some ala sites: {len(some_ala_sites)}")
combine_ala_sites = some_ala_sites + noway_sites
print(f"Combined unnecessary always-on sites: {len(combine_ala_sites)}")

# set(one_ala_cats)

# %%
from consent.consistency.util import normalize_cookie_category_name
import sys; import importlib; importlib.reload(sys.modules['consent.consistency.util'])
from consent.consistency.util import normalize_cookie_category_name
# def cat_normalize_cookie_category_name(acat):
#     ncat = normalize_cookie_category_name(acat).lower()
#     if 'functional' in ncat:
#         ncat = 'functional'
#     return ncat
combine_ala_cats = noway_cats + some_ala_cats
combine_ala_normalized_cats = [normalize_cookie_category_name(acat) for acat in combine_ala_cats]
Counter(combine_ala_normalized_cats).most_common()

# some_ala_sites

#%%
ot[ot.consent_mode == 'inactive landingpage'].site.nunique()
ot[ot.consent_mode == 'inactive landingpage'].site.unique()
# %%
