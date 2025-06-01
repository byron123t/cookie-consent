"""Generic results."""

from datetime import datetime

import mongoengine

from ooutil.crawler.error import Error


class ResultAbstract(mongoengine.Document):
    error = mongoengine.EmbeddedDocumentField(Error)
    warnings = mongoengine.ListField(mongoengine.StringField())

    timestamp = mongoengine.DateTimeField(default=datetime.utcnow)

    meta = {
        'allow_inheritance': True,
        'abstract': True
    }


class DefaultResult(ResultAbstract):
    meta = {
        'allow_inheritance': False
    }


def warning_msg(msg, warnings, print_msg):
    if warnings:
        warnings.append(msg)

    if print_msg:
        print(msg)
