"""Utilities for json handling."""

from datetime import datetime
# from http.cookiejar import domain_match, user_domain_match
import urllib.parse

from colorama import Fore


def chrome_domain_match(domain, host):
    # TODO: check compatible with Chrome cookie_util.cc https://bit.ly/2LbBRYJ
    if host == domain:
        return True

    # Domain cookie must have an initial ".".  To match, it must be
    # equal to url's host with initial period removed, or a suffix of
    # it.

    # Arguably this should only apply to "http" or "https" cookies, but
    # extension cookie tests currently use the funtionality, and if we
    # ever decide to implement that it should be done by preventing
    # such cookies from being set.
    if len(domain) == 0 or domain[0] != '.':
        return False

    if domain[1:] == host:
        return True

    # A pure suffix of the host (ok since we know the domain already
    # starts with a ".")
    return (len(host) > len(domain)) and (host[len(host) - len(domain):len(host)] == domain)

    # return domain_match(netloc, domain) fails on www.zeiss.com.tw and .zeiss.com
    # From https://github.com/python/cpython/blob/main/Lib/test/test_http_cookiejar.py
    # then user_domain_match is tested on "normal" domains than domain_match
    # using aiohttp still needs to modify domain.
    # if domain.startswith('.'): domain = domain[1:]
    # return aiohttp.cookiejar.CookieJar._is_domain_match(domain, netloc)

def url_domain_match(url, domain, path=None, verbose=2):
    """Return true if request_url domain-matches the `domain`."""
    urlparse = urllib.parse.urlparse(url)
    if path is not None and not urlparse.path.startswith(path):
        if verbose >= 2: print(f"Domain path mismatch: {domain} domain's path {path} not match url {url}")
        return False

    return chrome_domain_match(domain, urlparse.netloc)

def _test_url_domain_match():
    # https://source.chromium.org/chromium/chromium/src/+/master:net/cookies/cookie_util_unittest.cc;l=345
    assert chrome_domain_match('example.com', 'example.com')
    assert not chrome_domain_match('www.example.com', 'example.com')

    assert chrome_domain_match(".example.com", "example.com")
    assert chrome_domain_match(".example.com", "www.example.com")
    assert not chrome_domain_match(".www.example.com", "example.com")

    assert not chrome_domain_match("example.com", "example.de")
    assert not chrome_domain_match(".example.com", "example.de")
    assert not chrome_domain_match(".example.de", "example.de.vu")

    assert chrome_domain_match('.creative.com', 'creative.com')
    assert not chrome_domain_match('.zeiss.com', 'zeiss.com.tw')
    assert not chrome_domain_match('.zeiss.com', 'www.zeiss.com.tw')
    assert not chrome_domain_match('.zeiss.com.tw', 'www.zeiss.com')

    assert not url_domain_match('https://www.zeiss.com.tw/corporate/home.html', '.zeiss.com')

# def cookie_domain_match(cookie, domain):
#     """Check if the cookie's request_url domain-matches the `domain`."""
#     return url_domain_match(cookie['request_url'], domain)


def url_domain_match_any(url, domains):
    """Check if the cookie's request_url domain-matches the `domain`."""
    return any(url_domain_match(url, domain) for domain in domains)


def cookie_domain_match_any(cookie, domains):
    # return any(domain_match(cookie['domain'], domain) for domain in domains)
    return any(chrome_domain_match(domain, cookie['domain']) for domain in domains)


def get_domain_match_cookies(cookies, cookie_domains):
    """Return the cookie in cookies which domain-match cookie_domains.
    cookies is an array of dict {request_url: ..., cookie: ...}."""
    for cookie in cookies:
        if url_domain_match_any(cookie['request_url'], cookie_domains):
            yield cookie

"""
def parse_cookie(sent_cookie_raw):
    # parse cookie using the http cookie module, may not compat with what we dumped from Playwright as json
    cookie = SimpleCookie()
    try:
        cookie.load(sent_cookie_raw['cookie'])
    except CookieError as e:
        print(f'Error reading {sent_cookie_raw=}')
        print('Error:', str(e))

    for key, morsel in cookie.items():
        yield {'name': key, 'value': morsel.value, 'request_url': request_url}
        """


def get_expire_date(cookie):
    return datetime.fromtimestamp(cookie['expires'])

def get_expire_duration_in_days(cookie, from_time):
    time_diff = get_expire_date(cookie) - from_time
    return int(time_diff.days)

def get_expire_duration_from_now(cookie):
    time_diff = get_expire_date(cookie)- datetime.now()
    return int(time_diff.days)


def parse_cookie_str(cookie_str):
    """Parse our cookie dumps from PlayWright."""
    for acookie_str in cookie_str.split(';'):
        acookie_str = acookie_str.strip()
        try:
            if '=' not in acookie_str: # treat as a blank value, see: https://bit.ly/2XqZrUe
                key, val = acookie_str, ''
            else:
                key, val = acookie_str.split('=', 1)
            yield {'name': key, 'value': val}
        except ValueError as e:
            print(Fore.RED + f'Cannot parse {acookie_str=}' + Fore.RESET)
            print(Fore.RED + f'Error: {str(e)}' + Fore.RESET)


def get_brower_cookies(br_cookies_df, cookie, partial_value=None, verbose=0):
    """Get browser cookies which match a cookie."""
    found = br_cookies_df[ (br_cookies_df['name'] == cookie['name']) ]
    if partial_value is None:
        found = found[(found['value'] == cookie['value'])]
    else:
        found = found[found['value'].str.contains(partial_value)]

    if len(found) > 1:
        url_parts = urllib.parse.urlparse(cookie['request_url'])
        request_netloc, request_path = url_parts.netloc, url_parts.path
        found = found[ found.apply(lambda row: chrome_domain_match(row['domain'], request_netloc) and request_path.startswith(row['path']), axis=1) ]

        if len(found) > 1: # TODO get cookie at earliest creation time https://developer.chrome.com/docs/extensions/reference/cookies/
            if verbose >= 2: print(Fore.RED + f'WARNING: More than 1 match found:\nfound\n{found}\n{cookie=}' + Fore.RESET)
            found = found.sort_values(by=['path'], ascending=False).iloc[:1]
            if verbose >= 2: print(Fore.RED + f'Select the longest-match path:\nfound\n{found}\n{cookie=}' + Fore.RESET)
    return found


def legacy_get_brower_cookies(br_cookies_df, cookie, verbose=0):
    """Get browser cookies which match a cookie."""
    name, val = cookie['name'], cookie['value']
    found = br_cookies_df[ (br_cookies_df['name'] == name) & (br_cookies_df['value'] == val)]

    if len(found) > 1:
        url_parts = urllib.parse.urlparse(cookie['request_url'])
        request_netloc, request_path = url_parts.netloc, url_parts.path
        found = found[ found.apply(lambda row: chrome_domain_match(row['domain'], request_netloc) and request_path.startswith(row['path']), axis=1) ]

        if len(found) > 1: # TODO get cookie at earliest creation time https://developer.chrome.com/docs/extensions/reference/cookies/
            if verbose >= 2: print(Fore.RED + f'WARNING: More than 1 match found: {found=} {cookie=}' + Fore.RESET)
            found = found.sort_values(by=['path'], ascending=False).head(0)
            if verbose >= 2: print(Fore.RED + f'Select the longest-match path: {found=} {cookie=}' + Fore.RESET)
    return found

def get_kv_cookie(cookie):
    return {k: cookie[k] for k in ['name', 'value', 'domain', 'path']}


def get_kv_cookies(cookies):
    return [get_kv_cookie(cookie) for cookie in cookies]


if __name__ == '__main__':
    _test_url_domain_match()
    print('Test passed.')
