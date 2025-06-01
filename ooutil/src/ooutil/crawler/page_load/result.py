import mongoengine

from ooutil.crawler.result import ResultAbstract

class ChromeURLField(mongoengine.URLField):
    def validate(self, value):
        # Skip some special URLs of Chrome.
        if value not in ['about:blank']:
            super().validate(value)     # let IntField.validate run first


class PageLoadResultAbstract(ResultAbstract):
    """Store the result of preference button detection."""
    initial_url = mongoengine.URLField()
    # url = mongoengine.URLField()  # Assume this is URL of the main frame
    url = ChromeURLField()  # Assume this is URL of the main frame; sometimes it is about:blank

    # page_html = mongoengine.StringField()
    frames = mongoengine.ListField(mongoengine.DictField())  # Could not use mapping url -> {url, content} because MongoDb does not store keys with dot
    perf_timing = mongoengine.DictField(default=None)  # default of DictField is {}
    screenshot = mongoengine.StringField()
    cookies = mongoengine.ListField(mongoengine.DictField(), default=None)

    meta = {
        'allow_inheritance': True,
        'abstract': True
    }


class PageLoadResult(PageLoadResultAbstract):
    meta = {
        'allow_inheritance': False,
    }
