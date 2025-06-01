"""Utilities for dictionaries."""

from ooutil.type_util import hashabledict


def dicts_intersect(dict_list1, dict_list2):
    set1 = set(hashabledict(adict) for adict in dict_list1)
    set2 = set(hashabledict(adict) for adict in dict_list2)
    return len(set1.intersection(set2)) > 0


def dict_lists_equal(dict_list1, dict_list2):
    set1 = set(hashabledict(adict) for adict in dict_list1)
    set2 = set(hashabledict(adict) for adict in dict_list2)
    return set1 == set2


def dict_list_contain(dict_list, adict):
    """Assume dict list is short, so just linear search"""
    return any(adict == d for d in dict_list)


def dict_list_subset(dict_list, subset_dict_list):
    set1 = set(hashabledict(adict) for adict in dict_list)
    set2 = set(hashabledict(adict) for adict in subset_dict_list)
    return set2.issubset(set1)


def reverse_dict(adict):
    """Reverse a dict, checking that the values are unique."""
    reverse_dict = {}
    for k, v in adict.items():
        assert v not in reverse_dict, f"value {v} is not unique."
        reverse_dict[v] = k
    return reverse_dict


def test_dicts_equal():
    dicts1 = [{'a': 1}, {'b': 2}]
    dicts2 = [{'b': 2}, {'a': 1}]
    assert dict_lists_equal(dicts1, dicts2)

    dicts1 = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
    dicts2 = [{'b': 2}, {'a': 1}]
    assert not dict_lists_equal(dicts1, dicts2)

def test_dicts_subset():
    dicts1 = [{'a': 1}, {'b': 2}]
    dicts2 = [{'b': 2}]
    assert dict_list_subset(dicts1, dicts2)

    dicts1 = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
    dicts2 = [{'b': 2}, {'a': 1}]
    assert not dict_list_subset(dicts1, dicts2)


def main():
    test_dicts_equal()
    test_dicts_subset()
    print("Tests passed.")


if __name__ == '__main__':
    main()
