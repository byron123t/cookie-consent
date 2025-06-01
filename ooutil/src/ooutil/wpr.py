"""Utils for web page replay."""


def get_wpr_proxied_browser(p, headless: bool=True):
    return p.chromium.launch(args=['--host-resolver-rules="MAP *:80 127.0.0.1:8080,MAP *:443 127.0.0.1:8081,EXCLUDE localhost"',
                                   '--ignore-certificate-errors-spki-list=PhrPvGIaAMmd29hj8BCZOq096yj7uMpRNHpn5PDxI6I='],
                             headless=headless)
                             