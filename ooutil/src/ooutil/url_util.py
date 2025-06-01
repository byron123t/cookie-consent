"""Utilities for URLs."""

from typing import Iterable
from functools import lru_cache
from urllib.parse import urlparse
import base64
import re

from pathvalidate import sanitize_filename
from tldextract import extract


def get_file_name_from_url_path(url):
    """Get a proper file name from url, only path component of the url."""
    candid = ''.join(urlparse(url)[2:])
    candid = re.sub('[/> |:&?]', '_', candid)
    file_name = sanitize_filename(candid, replacement_text="_")[:200]  # caller may add some suffix.
    return file_name


def get_file_name(url):
    """Get a proper file name from url."""
    url_parts = urlparse(url)
    candid = url_parts.netloc + url_parts.path
    candid = re.sub('[/> |:&?]', '_', candid)
    file_name = sanitize_filename(candid, replacement_text="_")[:200]  # caller may add some suffix.
    return file_name

def remove_trailing_slash(astr):
    return astr[:-1] if astr.endswith('/') else astr

def remove_trailing_slash_urls(urls: Iterable[str]):
    return [remove_trailing_slash(url) for url in urls]

def get_hostname(url):
    url_parts = urlparse(url)
    return url_parts.hostname

def get_resource_name_from_url(url):
    """Return en.json from http://abc.com/some_path/en.json"""
    url_parts = urlparse(url)
    return url_parts.path.split('/')[-1]

def get_full_domain(url):
    """Get full domain name. Ignore empty parts."""
    ext = extract(url)
    # From doc: https://github.com/john-kurkowski/tldextract
    return '.'.join(part for part in ext if part)

def get_netloc_path(url, include_path=True, do_remove_trailing_slash=True):
    """Get netloc + path"""
    url_parts = urlparse(url.strip())
    path = remove_trailing_slash(url_parts.path) if do_remove_trailing_slash else url_parts.path
    result = url_parts.netloc
    if include_path:
        result += path
    return result

@lru_cache(maxsize=None)
def get_netloc(url):
    return urlparse(url.strip()).netloc

@lru_cache(maxsize=None)
def get_suffixed_domain(url):
    """Return only domain and its suffix."""
    ext = extract(url)
    if ext.suffix == '': # E.g., an ip address
        return None
    return ext.domain + '.' + ext.suffix
# def get_suffixed_domain(url):
#     return '.'.join(extract(url)[1:])

def get_suffixed_domain_with_dot_prefix(url):
    """Return only domain and its suffix."""
    return '.' + get_suffixed_domain(url)

def is_valid_domain(url):
    return get_suffixed_domain(url) is not None


def is_absolute(url):
    """Check absolute url, to avoid mailto:..."""
    return bool(urlparse(url).netloc)


def is_same_suffixed_domain(url1, url2):
    return get_suffixed_domain(url1) == get_suffixed_domain(url2)


def get_host(url):
    ext = extract(url)
    if ext[0] != '':
        return '.'.join(ext) # in case https://usnews.com
    else:
        return '.'.join(ext[1:])


def get_domain(url):
    ext = extract(url)
    return ext.domain


def add_protocol_if_needed(domain_or_url, add_www_if_needed=True):
    if not domain_or_url.startswith('http'):
        if add_www_if_needed and not domain_or_url.startswith('www'):
            domain_or_url = 'www.' + domain_or_url
        return 'http://' + domain_or_url
    return domain_or_url


def _get_home_page_urls_from_domain(domain):
    if domain.startswith('http://') or domain.startswith('https://'):
        print('WARNING: domain starts with http, just use the domain as the home page.')
        yield domain
    else:
        for protocol in ['https', 'http']:
            if not domain.startswith('www.'):
                for subdomain in ['www.', '']:
                    yield f'{protocol}://{subdomain}{domain}'
            else:
                    yield f'{protocol}://{domain}'


def get_home_page_urls_from_domain(site):
    home_page_urls = list(_get_home_page_urls_from_domain(site))
    if len(home_page_urls) == 0:
        raise ValueError('Cannot get home page urls from domain')
    assert all(url.startswith('http')
               for url in home_page_urls), f'{home_page_urls=} should start with http'

    return home_page_urls


def match_resource_paths(url_path, path_patterns):
    for pattern in path_patterns:
        if re.search(pattern, url_path):
            return True
    return False


def is_pdf(url):
    return urlparse(url).path.endswith('.pdf')


def try_decode_base64(v, verbose=0):
    try:
        if len(v) % 4:
            # not a multiple of 4, add padding:
            v += '=' * (4 - len(v) % 4)
        return base64.b64decode(v).decode('utf-8')
    except Exception as e:
        if verbose >= 2: print('Exception', e)

    return None


def get_urls_from_sites(sites):
    return [add_protocol_if_needed(site) for site in sites]


def remove_dot_prefix(astr):
    return astr[1:] if astr.startswith('.') else astr


def test_generate_urls_from_domain():
    domain = 'example.com'
    assert sorted(list(get_home_page_urls_from_domain(domain))) == sorted(['https://www.example.com', 'https://example.com', 'http://www.example.com', 'http://example.com'])
    domain = 'www.example.com'
    assert sorted(list(get_home_page_urls_from_domain(domain))) == sorted(['https://www.example.com', 'http://www.example.com'])
    domain = 'sub.example.com'
    assert sorted(list(get_home_page_urls_from_domain(domain))) == sorted(['https://www.sub.example.com', 'https://sub.example.com', 'http://www.sub.example.com', 'http://sub.example.com'])


def test_domains():
    ip = '67.87.111.22'
    assert get_suffixed_domain(ip) is None
    assert not is_valid_domain(ip)

    domain = 'rtcl.eecs.umich.edu'
    assert get_suffixed_domain(domain) is not None
    assert is_valid_domain(domain)


def test_decomposition():
    url = 'http://abc.com/some_path/en.json'
    assert get_resource_name_from_url(url) == 'en.json'
    url = 'https://consent.cookiebot.com/e33407d2-0296-4168-a6fb-6e38ce5f1ffb/cc.js?renew=false&referer=www.hltv.org&dnt=false&forceshow=false&cbid=e33407d2-0296-4168-a6fb-6e38ce5f1ffb&brandid=Cookiebot&framework=IABv2'
    assert get_resource_name_from_url(url) == 'cc.js'


def test_pdf_url():
    assert is_pdf('https://www.acm.org/binaries/content/assets/public-policy/europetpc-diggreencerts-stmt.pdf')
    assert is_pdf('https://www.acm.org/binaries/content/assets/public-policy/europetpc-diggreencerts-stmt.pdf?param1=1&param2=2')
    assert not is_pdf('https://www.acm.org/binaries/content/assets/public-policy/europetpc-diggreencerts-stmt.docx')
    assert not is_pdf('https://www.acm.org/binaries/')

if __name__ == '__main__':
    assert get_suffixed_domain('https://www.usnews.com') == 'usnews.com'
    assert get_host('https://www.usnews.com') == 'www.usnews.com'
    assert get_host('https://usnews.com') == 'usnews.com', f"{get_host('https://usnews.com')=}"
    print(get_file_name("https://www.google.com/search?q=max+file+name+length+linux&hl=en&source=lnms&tbm=nws&sa=X&ved=2ahUKEwjw0eqAr9DtAhXBXc0KHb9gDs0Q_AUoAXoECCEQAw&biw=2195&bih=1125"))

    assert is_same_suffixed_domain('http://abc.com', 'http://abc.com')
    assert is_same_suffixed_domain('http://abc.com', 'https://abc.com')
    assert is_same_suffixed_domain('http://www.abc.com', 'https://subpage.sub.abc.com')
    test_generate_urls_from_domain()

    test_domains()
    test_decomposition()
    test_pdf_url()

    print('Tests passed.')

