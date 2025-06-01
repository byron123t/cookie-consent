"""Check same origin.
https://github.com/synacor/python-cors/blob/master/cors/definitions.py
"""

import re
from urllib.parse import urlparse


def _normalize_origin_url(origin):
    origin_parts = urlparse(origin)
    origin = [origin_parts.scheme, "://", origin_parts.netloc]
    if not re.search(":\d+$", origin_parts.netloc):
        origin.append(":443" if origin_parts.scheme == "https" else ":80")
    return "".join(origin)


def is_same_origin(url1, url2):
    """ Whether or not the request origin matches the host. """
    return _normalize_origin_url(url1) == _normalize_origin_url(url2)


def _test():
    assert is_same_origin('https://nytimes.com', 'https://nytimes.com')
    assert is_same_origin('https://nytimes.com', 'https://nytimes.com/news')
    assert not is_same_origin('https://www.nytimes.com', 'https://nytimes.com/news')
    assert not is_same_origin('https://mail.google.com', 'https://www.google.com/')
    assert not is_same_origin('http://mail.google.com', 'https://mail.google.com/')
    assert is_same_origin('https://www.google.com', 'https://www.google.com/mail/auth/0/')


if __name__ == '__main__':
    _test()
    print("Tests passed.")
