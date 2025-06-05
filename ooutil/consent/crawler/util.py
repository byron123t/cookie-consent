"""Crawling utils."""

from consent.data.database.exper_result_database import ExperResultDatabase

BATCH_SIZE = 1000

def get_site_to_lang(exper_date, collection):
    done_lang = ExperResultDatabase(exper_date, collection).query_to_df()
    return {row['site']: row['lang'] for _, row in done_lang.iterrows()}

def get_continuous_ranks(site_rank_start, site_rank_end):
    return list(range(site_rank_start, site_rank_end + 1))


def split_site_ranks(site_ranks, batch_size=BATCH_SIZE):
    """Generate and split site ranks."""
    assert isinstance(site_ranks, list), 'site_ranks must be a list.'
    batch_size = len(site_ranks) if batch_size is None else batch_size
    results = []
    batch_start = 0
    while batch_start < len(site_ranks):
        results.append(site_ranks[batch_start:batch_start + batch_size])
        batch_start += batch_size
    return results
