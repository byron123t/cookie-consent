"""Manage connections to Mongo database."""

import mongoengine

from consent.data.database import mongo_config
from ooutil.database import exper_result

PROJECT_DB = 'consent_project'


class ExperResultRegistry(exper_result.ExperResultRegistry):
    """High-level connection based on mongoengine."""
    DB_ALIAS = PROJECT_DB
    _MONGO_URL = mongo_config.MONGO_URL
    _PROJECT_DB = PROJECT_DB


class CrawlDbExperResultRegistry(exper_result.ExperResultRegistry):
    """High-level connection based on mongoengine."""
    DB_ALIAS = PROJECT_DB
    _MONGO_URL = mongo_config.MONGO_CRAWL_DB_URL
    _PROJECT_DB = PROJECT_DB


class ExperResultDatabase(exper_result.ExperResultDatabase):
    _MONGO_URL = mongo_config.MONGO_URL
    _PROJECT_DB = PROJECT_DB

class CrawlDbExperResultDatabase(exper_result.ExperResultDatabase):
    _MONGO_URL = mongo_config.MONGO_CRAWL_DB_URL
    _PROJECT_DB = PROJECT_DB


def test_connection():
    mongoengine.connect(host=mongo_config.MONGO_URL)
    try:
        ExperResultRegistry._register_connection('2000-01-01')
    finally:
        ExperResultRegistry._disconnect()

def test_connection_crawl_db():
    mongoengine.disconnect() # disconnect prior connection
    mongoengine.connect(host=mongo_config.MONGO_CRAWL_DB_URL)
    try:
        ExperResultRegistry._register_connection('2000-01-01')
    finally:
        ExperResultRegistry._disconnect()


def test_non_existence():
    assert not ExperResultDatabase(
        '2021-07-04-test-non-exist', 'nonexist').exists()


if __name__ == '__main__':
    test_connection()
    test_connection_crawl_db()
    test_non_existence()
    print("Tests passed.")
