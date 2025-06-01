"""Get user agent for Chrome headless."""

from pathlib import Path

from user_agents import parse
from playwright.sync_api import Error, TimeoutError

user_agent_file = Path(__file__).parent / 'user_agent'

def _slow_get_headful_user_agent():
    """Launch a headless browser, then replace HeadlessChrome with Chrome, to get a headful the agent."""
    # print("user agent:", page.evaluate("navigator.userAgent"))
    pass

def get_stealth_user_agent(browser=None, verbose=0):
    # TODO: persistent to file, and update the useragent (change HeadlessChrome to Chrome)
    ua_string = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36"
    ua = parse(ua_string)

    # Just use a fixed user agent may be enough.
    if verbose >= 2 and browser and not browser.version.startswith(ua.browser.version_string):
        print(f'WARNING: ua_string browser version {ua.browser.version_string=} is different from actual browser version {browser.version=}, need to update ua_string')

    return ua_string


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        brcontext = browser.new_context()
        brcontext.clear_cookies()

        website = "http://google.com"

        page = brcontext.new_page()
        try:
            page.goto(website)
            print("user agent:", page.evaluate("navigator.userAgent"))
        except TimeoutError as e:
            print(f'Loading {website} timeout:', e)
        except Error as e:
            print(f'Loading {website} error:', e)

        browser.close()
