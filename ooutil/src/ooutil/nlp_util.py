"""Utils for managing nlp pipeline in the project."""

import diskcache as dc
import spacy


class _SpacyNlp:
    """Cached Spacy Nlp."""
    _nlp = None
    _nlp_lemmatizer = None

    @classmethod
    def _get_and_save_nlp(cls, nlp_var, nlp_class, verbose=0):
        _nlp = getattr(cls, nlp_var)
        if _nlp is None:
            if verbose >= 2: print(f'Loading {nlp_class} ...')
            _nlp = spacy.load(nlp_class)
            setattr(cls, nlp_var, _nlp)
            if verbose >= 2: print(f'Finished loading.')
        return _nlp

    @classmethod
    def get_nlp(cls):
        return cls._get_and_save_nlp('_nlp', nlp_class='en_core_web_trf')

    @classmethod
    def get_nlp_lemmatizer(cls):
        var_name = '_nlp_lemmatizer'
        nlp = getattr(cls, var_name)
        if nlp is None:
            nlp = cls._get_and_save_nlp(var_name, nlp_class='en_core_web_md') # medium for accurate, small 3.2.0 wrong on cookies -> cookies
            for pname in ['ner']:  # other pipelines are needed to compute lemmas.
                nlp.remove_pipe(pname)
        return nlp


def get_spacy_nlp():
    # return _SpacyNlp.get_nlp_small() if small else _SpacyNlp.get_nlp()
    return _SpacyNlp.get_nlp() # TODO: create a nlp_lemmatizer if small else _SpacyNlp.get_nlp()


def get_dep_child(token, dep):
    for c in token.children:
        if c.dep_ == dep:
            return c
    return None

w_words = ['once', 'if', 'after', 'when', 'how', 'why']

def get_parent_advcl(token):
    """Return parental adverbial clause of an opt token."""
    doc = token.doc
    w_word = get_dep_child(token, 'mark') or get_dep_child(token, 'advmod')
    if w_word and w_word.lower_ in w_words and token.dep_ == 'advcl':
        head = token.head
        return doc[head.left_edge.i : head.right_edge.i+1]
    return None


def is_under_wword_clause(token):
    w_word = get_dep_child(token, 'mark') or get_dep_child(token, 'advmod')
    return w_word and w_word.lower_ in w_words


def search_verb_head(tok):
    """Recursively go back to parrent to get the verb token."""
    if tok is None or tok == tok.head:  # Reach the root.
        return tok

    if tok.pos_ == 'VERB':
        return tok

    return search_verb_head(tok.head)

class CachedLemmatizer:
    _cache = dc.Cache('/tmp/lemmatizer.cache')

    @classmethod
    def lemmatize_lower_pron(cls, astring: str):
        lemmas = cls._cache.get(astring)
        if lemmas is None:
            lemmas = lemmatize(astring, lower_pron=True)
            cls._cache[astring] = lemmas
        return lemmas


def lemmatize(astring: str, lower_pron=True):
    """Return a list of lemmas from a plain-text string."""
    nlp = _SpacyNlp.get_nlp_lemmatizer() # use small for efficiency
    lemmas = []
    for t in nlp(astring):
        lemma = t.lemma_
        if lower_pron and lemma == '-PRON-':
            lemma = t.lower_
        lemmas.append(lemma)
    return lemmas

def get_spaced_lemma(text):
    """Return space-separated lemmas of the text."""
    return ' '.join(lemmatize(text))


# def get_opt_matcher(cls):
#     """Return the matcher which finds the opt-out or opt verb."""
#     matcher = cls._opt_verb_matcher
#     if matcher is None:
#         matcher = Matcher(nlp.vocab)
#         pattern = [{"LEMMA": "opt", "POS": "VERB"}]
#         matcher.add("opt", [pattern])
#         cls._opt_verb_matcher = matcher
#     return matcher

if __name__ == '__main__':
    assert get_spaced_lemma('cookies settings') == 'cookie setting', f"Got {get_spaced_lemma('cookies settings')}"
    assert get_spaced_lemma('Cookies Settings') == 'cookie setting', f"Got {get_spaced_lemma('Cookies Settings')}"
    assert CachedLemmatizer.lemmatize_lower_pron('Cookies Settings') == ['cookie', 'setting']
    print(CachedLemmatizer.lemmatize_lower_pron('Terms & Conditions'))
    print(CachedLemmatizer.lemmatize_lower_pron('Manage Your Settings'))
    print('Tests passed.')

# %%
