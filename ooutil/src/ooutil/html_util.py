"""HTML utilities."""

import re

from bs4 import BeautifulSoup
from html2text import HTML2Text
import html5lib  # to generate requirements.txt
import markdown
# import mistletoe
import requests


# Based on https://github.com/EdwardJRoss/job-advert-analysis/blob/cc_pipeline/notebooks/Converting%20HTML%20to%20Text.ipynb
# and https://www.digitalocean.com/community/tutorials/how-to-use-python-markdown-to-convert-markdown-text-to-html
def html2md(html):
    parser = HTML2Text()
    parser.ignore_images = True
    parser.ignore_anchors = True
    parser.body_width = 0
    md = parser.handle(html)
    return md


def html2plain(html, parser='html5lib'):
    """parser: can change to lxml for faster speed."""

    # HTML to Markdown
    md = html2md(html)
    # Normalise custom lists
    md = re.sub(r'(^|\n) ? ? ?\\?[•·–-—-*]( \w)', r'\1  *\2', md)
    # Convert back into HTML
    html_simple = markdown.markdown(md) # markdown: more stars on github than mistletoe
    # html_simple = mistletoe.markdown(md)
    # Convert to plain text
    soup = BeautifulSoup(html_simple, features=parser)
    text = soup.getText()
    # Strip off table formatting
    text = re.sub(r'(^|\n)\|\s*', r'\1', text)
    # Strip off extra emphasis
    text = re.sub(r'\*\*', '', text)
    # Remove trailing whitespace and leading newlines
    text = re.sub(r' *$', '', text)
    text = re.sub(r'\n\n+', r'\n\n', text)
    text = re.sub(r'^\n+', '', text)
    return text


def get_html_text(url):
    """Return html from URL."""
    return requests.get(url).text


def get_plain_text(url):
    return html2plain(get_html_text(url))


def test():
    # url = 'https://www.wsj.com'
    # url = 'https://www.adxpose.com/home.page' #
    url = 'https://triggerbee.com/'  # maybe harder case
    url = 'http://www.dotdigitalgroup.com/'
    url = 'https://adonly.com'
    html = requests.get(url, verify=False).text
    print(html2plain(html))
    # print(get_plain_text(url))


if __name__ == '__main__':
    test()
