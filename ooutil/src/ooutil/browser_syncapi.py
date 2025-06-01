"""Utility for browsers."""

from pathlib import Path
from playwright.sync_api import Browser, Page, sync_playwright, TimeoutError
import time

from ooutil.file import file_exists_not_empty_and_old
from ooutil.user_agent import get_user_agent
from ooutil.wpr import get_wpr_proxied_browser


def get_realistic_context(browser: Browser):
    """Set appropriate user agent. viewport={width: int, heigh: int}"""
    return browser.new_context(user_agent=get_user_agent(browser))


def navigate_and_wait_network(page: Page, url):
    try:
        page.goto(url=url, wait_until='networkidle', timeout=20000)
    except TimeoutError as e:
        print('Warning: Navigation timeout') 
    except Exception as e:
        print('Warning: Fail to load', type(e), e) 
        return False

    try:
        # Check if the page is loaded properly.
        body_text = page.text_content('body', timeout=20000)
        if body_text is None:
            raise ValueError(f'Cannot retrieve body text. {page.content()=}')
        else:
            # Some cases: tencent.com: body empty.
            if len(body_text) == 0:
                raise ValueError(f'Body is empty. {page.content()=}')
    except Exception as e: # including cannot get the body within timeout.
        print('Warning: to load', type(e), e) 
        return False

    return True


def _screenshot(browser: Browser, url: str, out_file: Path, post_navigate_hook=None, shot_footer=False):
    """Take screenshot with a clean browser context."""
    brcontext = get_realistic_context(browser)
    page = brcontext.new_page()
    try:
        if not navigate_and_wait_network(page, url):
            return False

        if post_navigate_hook is not None:
            post_navigate_hook(page)

        time.sleep(3) # some banner is slow to show.
        if out_file.suffix == '.html':
            out_file.write_text(page.content())
            print(f'Written html to {out_file}')
        else:
            page.screenshot(path=out_file, timeout=20000)
            print(f'Written screenshot to {out_file}')

        if shot_footer:
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3) # It may take some time to render.
            page.screenshot(path=out_file.parent / (out_file.stem + "_footer.png"), timeout=20000)

        return True
    except TimeoutError as e:
        print('Warning: Screenshot timeout', e) 
    finally:
        page.close()
        brcontext.close()
    return False


def screenshot(browser, url, out_file, post_navigate_hook=None, shot_footer=False):
    if _screenshot(browser, url, out_file, post_navigate_hook, shot_footer):
        print(f'Save screenshot of {url} to {out_file.name}' + (' and footer' if shot_footer else ''))
    else:
        print(f'Failed to save screenshot of {url}')


def _save_screenshots_thread_safe(browser, rank_domains, urls, out_dir: Path, post_navigate_hooks=None, shot_footer=False, dry_run=False, save_format='.png', verbose=2):
    """Save screenshots with support for multiple workers (thread-safe)."""
    assert len(urls) == len(rank_domains)
    if post_navigate_hooks is not None:
        assert len(urls) == len(post_navigate_hooks)

    for i, ((rank, domain), url) in enumerate(zip(rank_domains, urls)):
        if verbose >= 2: print(f"Process {domain}")

        out_file = out_dir / f'{rank}-{domain}'
        out_file = out_file.with_suffix(save_format)
        # Hack: uncomment to save html.
        # out_file = out_file.with_suffix('.html')
        if file_exists_not_empty_and_old(out_file):
            if verbose >= 3: print(f"Already shot, skip {domain}")
            continue


        post_navigate_hook = post_navigate_hooks[i] if post_navigate_hooks is not None else None
        if dry_run:
            print(f'Screenshot {rank=} {domain=} {url=} {post_navigate_hook=} to {out_file=}')
            continue

        out_file.touch()
        screenshot(browser, url, out_file, post_navigate_hook, shot_footer)


def save_screenshots_thread_safe(rank_domains, urls, out_dir: Path, post_navigate_hooks=None, shot_footer=False, use_wpr=False, headless=False, dry_run=False, save_format='.png'):
    with sync_playwright() as p:
        if use_wpr:
            browser = get_wpr_proxied_browser(p, headless=headless)
        else:
            browser = p.chromium.launch(headless=headless)
        
        _save_screenshots_thread_safe(browser, rank_domains, urls, out_dir, post_navigate_hooks, shot_footer, dry_run, save_format)


def scroll_to_bottom(page: Page):
    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")


def navigate_homepages(page, domain, dry_run=False, verbose=2):
    """Best effort navigate and wait. Handle multiple cases.
    Try 4 combinations of URLs of the home page."""
    for protocol in ['http', 'https']:
        for subdomain in ['', 'www.']:
            url = f'{protocol}://{subdomain}{domain}'
            if verbose >= 2: print('Go to', url)

            if navigate_and_wait_network(page, url):
                return True
                
    return False


if __name__ == '__main__':
    navigate_homepages(None, 'google.co.uk')