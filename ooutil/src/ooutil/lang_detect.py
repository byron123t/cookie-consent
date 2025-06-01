"""Detect language"""

import gcld3
import langdetect


from ooutil.html_util import html2plain
from ooutil.crawler.error import get_error_dict_from_exception


def detect_lang_text(text, verbose=0):
    """Detect language of text. Param explanation: https://bit.ly/3w2G0Ql
    Return detected lang, reliable/unreliable, proportion of the detected lang, confidence.
    Language code: https://github.com/google/cld3"""
    detector = gcld3.NNetLanguageIdentifier(
        min_num_bytes=0, max_num_bytes=1000)
    # , result.proportion, result.probability
    result = detector.FindLanguage(text=text)
    if result.is_reliable:
        return result.language

    langdetect.DetectorFactory.seed = 1025
    # TODO: add confidence (probability) of langdetect and return None if it is too low.
    lang = langdetect.detect(text)
    if verbose >= 3:
        print('CLD3 lang:', result.language, '; langdetect:', lang)
    return lang


def detect_lang_html(html, verbose=0):
    """Detect language pipeline: html -> text -> detect lang."""
    # text = html2text.html2text(html)
    try:
        text = html2plain(html)

        if verbose >= 3:
            print('Text:', text)
        return detect_lang_text(text)
    except Exception as e:
        print(f'Error detetcting lang', get_error_dict_from_exception(e))
    return None


def test():
    lang = detect_lang_text(
        'The quick brown fox jumps over the lazy dog.')
    assert lang == 'en', f"Unexpected {lang=}"


def test_html():
    import requests
    # url = 'https://www.wsj.com'
    # url = 'https://www.adxpose.com/home.page' #
    # url = 'https://triggerbee.com/'  # maybe harder case
    url = 'https://www.kwanko.com/'
    url = 'https://adonly.com'
    url = 'https://www.webterren.com/'
    url = 'https://www.winaffiliates.com/'
    html = requests.get(url).text
    print('Lang:', detect_lang_html(html))


if __name__ == '__main__':
    test()
    test_html()
    print('Tests passed.')
