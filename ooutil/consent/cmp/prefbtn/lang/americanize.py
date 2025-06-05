"""Convert American English to British English
Based on https://raw.githubusercontent.com/hyperreality/American-British-English-Translator/master/data/british_spellings.json
"""

from pathlib import Path
from functools import lru_cache
from typing import Dict
import json

from consent.cmp.prefbtn.pref_btn_featurizer import pref_unigrams, all_pref_bigrams, pref_bigrams_likely


@lru_cache()
def get_gb_to_us() -> Dict[str, str]:
    data_file = Path(__file__).parent / 'british_spellings.json'
    # print(f"Read {data_file}")
    # Reduce the dictionary to only the keywords
    gb_to_us = json.loads(data_file.read_text())
    us_to_gb = {v:k for k, v in gb_to_us.items()}
    reduced_dict = {}
    for gram in pref_unigrams.union(all_pref_bigrams.union(pref_bigrams_likely)):
        for token in gram.split():
            token = token.strip()
            if token in us_to_gb:
                reduced_dict[us_to_gb[token]] = token

    return reduced_dict


def americanize(string):
    british_to_american = get_gb_to_us()
    # print(british_to_american)
    # return british_to_american.get(string, string)
    for british_spelling, american_spelling in british_to_american.items():
        string = string.replace(british_spelling, american_spelling)
    return string


def test():
    assert americanize('customise') == 'customize'
    # assert americanize('centre') == 'center' # not in the dict
    # assert americanize('millimetre') == 'millimeter' # not in the dict


if __name__ == '__main__':
    test()
    print("Tests passed.")
