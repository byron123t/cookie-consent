
def read_prerej_sent_cookies(data_dir, keep_sent_cookie=False):
    """Assume structured data_dir /site / data_files. Could not aggregate sent cookies to reduce computation because we need to map to the same state of browser cookies."""
    cookies_files = list(data_dir.glob('*/prerej_cookies.json'))[:]
    raise NotImplementedError('Need to reimplement')
    return parallel_read_sent_cookies(cookies_files, keep_sent_cookie)
