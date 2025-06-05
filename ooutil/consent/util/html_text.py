"""Get plain text from html.
From https://rushter.com/blog/python-fast-html-parser/
"""

from bs4 import BeautifulSoup
import lxml # keep this to generate requirements, without lxml, bs4 will fail

def get_text(html):
    tree = BeautifulSoup(html, 'lxml')

    body = tree.body
    if body is None:
        return None

    for tag in body.select('script'):
        tag.decompose()
    for tag in body.select('style'):
        tag.decompose()

    text = body.get_text(separator='\n')
    return text


# TODO: Test this to see whether it is faster or not.
# from selectolax.parser import HTMLParser
# def get_text_selectolax(html):
#     tree = HTMLParser(html)

#     if tree.body is None:
#         return None

#     for tag in tree.css('script'):
#         tag.decompose()
#     for tag in tree.css('style'):
#         tag.decompose()

#     text = tree.body.text(separator='\n')
#     return text
