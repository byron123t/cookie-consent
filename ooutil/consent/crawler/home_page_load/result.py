"""Model the result of preference button detection."""

import mongoengine
from consent.data.database.exper_result_database import ExperResultRegistry
from ooutil.crawler.page_load.result import PageLoadResultAbstract


class HomePageLoadResult(PageLoadResultAbstract):
    site = mongoengine.StringField()

    screenshot_bottom = mongoengine.StringField()
    location = mongoengine.StringField(default='us')

    meta = {
        'db_alias': ExperResultRegistry.DB_ALIAS,
        'allow_inheritance': False,
    }
