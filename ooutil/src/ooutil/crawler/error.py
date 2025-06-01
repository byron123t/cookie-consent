"""Generic errors of crawlers."""

import traceback

import mongoengine


class Error(mongoengine.EmbeddedDocument):
    reason = mongoengine.StringField()
    exception = mongoengine.StringField()
    traceback = mongoengine.StringField()

    @classmethod
    def from_exception(cls, e):
        return Error(reason=str(e), exception=type(e).__name__, traceback=traceback.format_exc())


# Util functions.
def get_error_dict_from_exception(e):
    return {'reason': str(e).splitlines(), 'exception': type(e).__name__, 'traceback': traceback.format_exc().splitlines()}
