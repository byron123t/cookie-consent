#%%
"""Cookie matching algorithms."""

import fnmatch
import re

from typing import Dict
import tldextract

from ooutil.cookie_util import url_domain_match, chrome_domain_match


def relax_check_url_host_match(url: str, host: str):
    host = host.lower()
    if '.' not in host:
        return tldextract.extract(url).domain == host

    if url_domain_match(url, host):
        return True

    if not host.startswith('.') and url_domain_match(url, '.' + host):
        return True

    return False


def strict_check_url_host_match(url, host):
    host = host.lower()
    if '.' not in host:
        return tldextract.extract(url).domain == host

    return url_domain_match(url, host)


def resolve_host_declaration(cookie_pref: Dict, site):
    cookie_pref_host = cookie_pref['domain'].lower()
    if '.' in cookie_pref_host:
        host = cookie_pref_host
    # elif tldextract.extract(site).domain == cookie_pref_host:
        # host = site
    else:
        cookie_pref_domain = tldextract.extract(cookie_pref_host).domain
        if cookie_pref_domain != '':
            host = cookie_pref_domain
        else:
            raise ValueError(f"Invalid host {cookie_pref['domain']}")
    return host


def check_domain_pref_match(cookie_domain: str, pref_domain: str, verbose=0):
    def remove_leading_dot(name):
        return name[1:] if name.startswith('.') else name

    if verbose >= 3: print(f'{cookie_domain=} {pref_domain=}')

    cookie_domain = cookie_domain.lower()
    pref_domain = pref_domain.lower()  # Some hosts are declared with capitalized letters

    if '.' not in pref_domain:
        return (tldextract.extract(cookie_domain).domain == pref_domain)

    return remove_leading_dot(cookie_domain).endswith(remove_leading_dot(pref_domain))
    # return remove_leading_dot(pref_domain) == remove_leading_dot(cookie_domain)

    # Experimental ...
    if not pref_domain.startswith('.'):
        pref_domain = '.' + pref_domain

    return chrome_domain_match(pref_domain, remove_leading_dot(cookie_domain))

    if tldextract.extract(cookie_domain).domain == pref_domain:
        return True

    return False
    # if domain == host:
    #     return True
    # if domain.startswith('.'):
    #     domain = domain[1:]
    # if host.startswith('.')
    # assert not domain.startswith('.')
    # return domain == host

def replace_suffix_with_qm(astr, suffix_char):
    astr = list(astr)
    i = len(astr) - 1
    while i >= 0:
        if astr[i] == suffix_char:
            astr[i] = '?'
            i -= 1
        else:
            break
    return ''.join(astr)

def fuzzy_name_match(pref_name: str, cookie_name: str, verbose=0):
    # pref_name = pref_name.replace('*', '.*')
    # if verbose >= 3: print(f'{pref_name=}, {cookie_name=}')
    # pref_name = re.sub('xxxx*$', '*', pref_name)
    # pref_name = re.sub('XX+', '*', pref_name)
    if pref_name.endswith('xxx'):
        pref_name = replace_suffix_with_qm(pref_name, 'x')
    if pref_name.endswith('XXX'):
        pref_name = replace_suffix_with_qm(pref_name, 'X')

    if pref_name.endswith('###'):
        pref_name = replace_suffix_with_qm(pref_name, '#')
    elif pref_name.endswith('#') and not pref_name.endswith('##'):
        pref_name = re.sub('#+', '*', pref_name)

    if verbose >= 2: print(f'{pref_name=}, {cookie_name=}')

    try:
        # return re.match(pref_name, cookie_name) is not None
        return fnmatch.fnmatchcase(cookie_name, pref_name)

    except Exception as e:
        print(f'Error fuzzy name match {pref_name=} {cookie_name=}', e, )
    return False

def cookie_pref_match(cookie, cookie_pref, site: str, fuzzy_name=True, verbose=0):
    """Check whether cookie match cookie pref on site."""
    site = site.lower()

    try:
        cookie_pref_domain = resolve_host_declaration(cookie_pref, site)
    except ValueError as e:
        # print("Error", e)
        return False

    if verbose >= 2: print(f'{cookie=}\n{cookie_pref=}\n{cookie_pref_domain=}')
    # assert '.' in host # Use site as default; too strict, glassdoor should be included in many cases.
    # check_url_host_match(acookie['request_url'], host):
    # assert cookie['name'] == cookie_pref['name'] # Test

    # return cookie['name'] == cookie_pref['name']
    if fuzzy_name:
        name_match = fuzzy_name_match(cookie_pref['name'], cookie['name'])
    else:
        name_match = cookie['name'] == cookie_pref['name']
    return name_match and check_domain_pref_match(cookie['domain'], cookie_pref_domain)
    # return cookie['name'] == cookie_pref['name'] and (check_domain_pref_match(cookie['domain'], cookie_pref_domain) or check_domain_pref_match(cookie_pref_domain, cookie['domain']))


def test_check_url_host_match():
    url_hosts = [
        ('https://www.abc.com/apath', 'abc', True),
        ('https://www.abc.com/apath', '.abc.com', True),
        # ambiguous cases
        ('https://www.abc.com/apath', 'abc.com', False),  # strict
        # ('https://www.abc.com/apath', 'abc.com', True), # Relax
        ('https://subsite.abc.com/', 'www.abc.com', False)
    ]

    for url, host, expect_res in url_hosts:
        assert strict_check_url_host_match(
            url, host) == expect_res, f'{url=} {host=} {strict_check_url_host_match(url, host)=} != {expect_res=}'


def test_domain_pref_match():
    domain_and_pref_domains = [
        ('abc.com', 'abc.com', True),
        ('.abc.com', 'abc.com', True),
        ('.www.abc.com', 'abc.com', True),
        ('.abc.com', '.abc.com', True),
        ('www.abc.com', '.abc.com', True),
        # ('abc.com', '.abc.com', False),
        ('.www.abc.com', '.abc.com', True),
        ('www.abc.com', 'abc', True),
        ('www.abc.com', 'com', False),
        ('www.abc.com', 'www', False),
        ('www.abc.com', 'subsite.abc.com', False),
        ('.abc.com', 'subsite.abc.com', False),
        ('subsite.abc.com', '.abc.com', True)
    ]

    for domain, pref_domain, expect_res in domain_and_pref_domains:
        result = check_domain_pref_match(domain, pref_domain)
        assert result == expect_res, f'{domain=} {pref_domain=} {result=} != {expect_res=}'

def test_fuzzy_name_match():
    assert fuzzy_name_match('abc', 'abc')
    assert not fuzzy_name_match('abcxxx', 'abc')
    assert fuzzy_name_match('abcxxx', 'abc123')
    assert not fuzzy_name_match('abcXXX', 'abc')
    assert not fuzzy_name_match('abcXXX', 'abcds')
    assert not fuzzy_name_match('abcXXX', 'abcd123')
    assert not fuzzy_name_match('abcXXX', 'abcds123')
    assert not fuzzy_name_match('__utmvxxxx', '__utmvc')
    assert not fuzzy_name_match('__utmvXXXX', '__utmvc')
    assert fuzzy_name_match('__utmvxxxx', '__utmvc123')
    assert fuzzy_name_match('__utmvXXXX', '__utmv1234')
    assert fuzzy_name_match('__utmv*', '__utmvc')
    assert fuzzy_name_match('abc*', 'abc')
    assert fuzzy_name_match('_gat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', '_gat_4146069c195cb451d85e50c0aeff6b18')
    assert not fuzzy_name_match('_gat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', '_gat_acl')
    assert fuzzy_name_match('_ga#', '_ga123')
    assert not fuzzy_name_match('_ga####', '_ga123')
    assert fuzzy_name_match('_ga###', '_ga123')

if __name__ == '__main__':
    test_check_url_host_match()
    test_domain_pref_match()
    test_fuzzy_name_match()
    print("Tests passed.")

#  %%
