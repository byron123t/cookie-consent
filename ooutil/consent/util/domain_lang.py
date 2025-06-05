"""Util to get language of a website."""

from consent.util.default_path import get_data_dir

import pandas as pd

class DomainLang:
    _domain_to_lang = None

    @classmethod
    def get_lang_map(cls):
        if cls._domain_to_lang is None:
            data_dir = get_data_dir('2021-02-09')
            lang_file = data_dir / 'website_lang_1_5000.tsv'
            assert lang_file.exists()
            lang_df = pd.read_csv(lang_file, sep='\t')
            domain_to_lang = {}
            for _, row in lang_df.iterrows():
                domain = row['domain']
                assert domain not in domain_to_lang
                domain_to_lang[domain] = row['language']
            cls._domain_to_lang = domain_to_lang
        return cls._domain_to_lang

    @classmethod
    def get_lang(cls, domain: str):
        return cls.get_lang_map().get(domain)


def get_lang(domain):
    return DomainLang.get_lang(domain)

def is_domain_en(domain):
    return get_lang(domain) == 'en'

##############################
# Tests.
def test():
    assert get_lang('google.com') == 'en'
    assert get_lang('tmall.com') == 'zh-cn'
    assert is_domain_en('google.com')


if __name__ == '__main__':
    test()
    print('Tests passed.')
