"""Manage cookie settings."""

from pathlib import Path

from yaml import load, FullLoader
import pandas as pd

from ooutil.url_util import get_suffixed_domain


def map_pref_buttons(opt_setting):
    pref_buttons = []
    if not isinstance(opt_setting, list):
        print('WARNING: opt_setting is not a list:', opt_setting)
        return pref_buttons
    for setting in opt_setting:
        if isinstance(setting, dict) and 'pref_btn' in setting:
            pref_btn = setting['pref_btn']
            if pref_btn != '':
                pref_buttons.append(setting['pref_btn'])
    return pref_buttons


class CookieSetting:
    # Cached cookie setting data frame.
    _cookieset = None
    cookie_setting_files = [Path(__file__).parent / 'cookie_setting.yml', Path(__file__).parent / 'cookie_setting_eu2.yml']

    @classmethod
    def invalidate_cache(cls):
        cls._cookieset = None

    @classmethod
    def get_cookie_settings(cls, nocache=False, pref_btn_only=True, cookie_setting_files=None):
        def get_site(row):
            if not pd.isna(row['site']):
                return row['site']
            return get_suffixed_domain(row['opt_page'])

        cookieset = cls._cookieset
        if cookie_setting_files is None:
            cookie_setting_files = cls.cookie_setting_files

        if nocache or cookieset is None:
            dfs = [pd.DataFrame(load(cookie_setting_file.read_text(), Loader=FullLoader)) for cookie_setting_file in cookie_setting_files]
            cookieset = pd.concat(dfs)
            no_opt_settings = cookieset[cookieset['opt_setting'].isna()]

            if len(no_opt_settings):
                print("WARNING: Some sites have no opt_setting")
                print(no_opt_settings)

            cookieset['pref_buttons'] = cookieset.opt_setting.map(map_pref_buttons)

            cookieset['site'] = cookieset.apply(get_site, axis=1)
            assert len(cookieset[cookieset['opt_page'].isna()]
                       ) == 0, "Some page has missing opt_page."
            cls._cookieset = cookieset

        if pref_btn_only and "no_cookie_setting_on_home_page" in cookieset.columns:
            cookieset = cookieset[cookieset.no_cookie_setting_on_home_page.isna()]

        return cookieset

    @classmethod
    def get_field(cls, site, field):
        df = cls.get_cookie_settings()
        found = df[df.site == site]
        if len(found) == 0:
            return None
        assert len(found) == 1, f'{found=} should be a single row.'
        return found[field].iloc[0]

    @classmethod
    def get_consent_lib(cls, site):
        return cls.get_field(site, 'consent_lib')

    @classmethod
    def get_opt_page(cls, site):
        return cls.get_field(site, 'opt_page')

    @classmethod
    def get_first_pref_button(cls, site):
        pref_buttons = cls.get_field(site, 'pref_buttons')
        if len(pref_buttons) == 0:
            return None
        return pref_buttons[0]

    @classmethod
    def get_sites_with_consent_lib(cls, consent_lib: str):
        """Return sites that use the provided consent library."""
        df = cls.get_cookie_settings()
        return df[df.consent_lib == consent_lib].site.to_list()

    @classmethod
    def get_all_sites(cls):
        return cls.get_cookie_settings().site.to_list()

    @classmethod
    def get_all_consent_libs(cls):
        """Return the list of consent libs."""
        df = cls.get_cookie_settings()
        return sorted(df.consent_lib.unique())

    @classmethod
    def get_opt_pages(cls, sites=None):
        if sites is None:
            return cls.get_cookie_settings().opt_page.to_list()
        return [cls.get_opt_page(site) for site in sites]

    @classmethod
    def get_sites_with_pref_btn(cls):
        cookset = cls.get_cookie_settings()
        return cookset[cookset.pref_buttons.map(lambda buttons: len(buttons) > 0)].site.to_list()


if __name__ == '__main__':
    cooks = CookieSetting.get_cookie_settings(pref_btn_only=False)
    print(f"Num cookie settings sites: {len(cooks)}")
    vc = cooks.site.value_counts()
    assert len(cooks) == cooks.site.nunique()

    cooks = CookieSetting.get_cookie_settings(pref_btn_only=True)
    print(f"Num cookie settings sites with pref btns: {len(cooks)}")

    print("Tests passed.")
    # sites_with_pref_btn = CookieSetting.get_sites_with_pref_btn()
    # print("Num sites with pref btn:", len(sites_with_pref_btn))
    # print(sites_with_pref_btn)
