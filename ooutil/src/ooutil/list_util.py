"""Utils to handle lists."""
from typing import Any, Iterable, List
from itertools import groupby


def flatten_maybe_none_lists(lists: Iterable[List[Any]]):
    """Combine lists into a"""
    result = []
    for alist in lists:
        if alist is not None:
            result.extend(alist)
    return result



def all_equal(iterable):
    # https://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical
    """Check all items have equal values."""
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def all_unique(alist):
    """Check all items have different values."""
    return len(set(alist)) == len(alist)


def print_stats(things, description, limit_print=10):
    print(f"Num {description}: {len(things):,d}")

    if limit_print is not None:
        print(list(things)[:limit_print])
