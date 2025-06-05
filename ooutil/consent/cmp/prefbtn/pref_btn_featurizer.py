#%%
"""Featurize preference buttons."""
# Also see historic file: https://github.com/ducalpha/optout_project/blob/59a88b254167592fe76df397afaf7faaf9a85ac1/src/consent/cmp/pref_btn_text_notebook.ipynb

from typing import Callable, Optional
from spacy.lang.en.stop_words import STOP_WORDS
import numpy as np
import re

from ooutil.nlp_util import CachedLemmatizer


def _get_bigrams(lemmas):
    return [lemmas[i-1] + ' ' + lemmas[i] for i in range(1, len(lemmas))]


def tokenize_text(text, localize: Optional[Callable[[str], str]]=None, verbose=0):
    if text is None or len(text) == 0:
        return []
    text = text.lower()
    text = ' '.join(text.strip().split()) # Avoid middle multiple line breaks?
    lemmas = CachedLemmatizer.lemmatize_lower_pron(text)
    lemmas = [lemma.lower() for lemma in lemmas]
    lemmas = [lemma for lemma in lemmas if lemma.isalpha() and lemma not in STOP_WORDS] # remove non-alphabet string
    if localize is not None:
        lemmas = [localize(lemma) for lemma in lemmas]
    bigrams = _get_bigrams(lemmas)
    results = lemmas + bigrams
    if verbose >= 3:
        print(f'tokenize text: {results}')
    return results


def tokenize_classid(classid):
    """Tokenize a class/id identifier."""
    if not isinstance(classid, str):
        return []
    classid = classid.lower()
    classid = re.split('[_-]+', classid)
    lemmas = []
    for c in classid:
        lemmas.extend(CachedLemmatizer.lemmatize_lower_pron(c))
    return lemmas + _get_bigrams(lemmas)


# pref_unigrams = {'adchoice', 'adjust', 'california', 'change', 'choice', 'choose', 'configure', 'consent', 'cookie', 'customise', 'customize', 'individual', 'manage', 'option', 'personal', 'pref', 'preference', 'privacy', 'review', 'setting', 'update', 'view'}
# all_pref_bigrams = {'advanced setting', 'california sell', 'change privacy', 'change setting', 'consent choice', 'consent tool', 'cookie consent', 'cookie preference', 'cookie setting', 'individual privacy', 'let choose', 'manage cookie', 'manage preference', 'manage setting', 'personal information', 'privacy preference', 'privacy setting', 'review cookie', 'sell info', 'sell personal', 'set preference', 'update preference', 'view cookie', 'configure consent', 'consent detail'}
# With eu2
pref_unigrams = {'ad', 'adchoice', 'adjust', 'base', 'change', 'choice', 'choose', 'click', 'configuration', 'configure', 'consent', 'cookie', 'customise', 'customize', 'datum', 'detail', 'gdpr', 'individual', 'info', 'information', 'interest', 'learn', 'let', 'manage', 'manager', 'manually', 'modal', 'open', 'opt', 'option', 'parameter', 'personal', 'personalize', 'policy', 'preference', 'privacy', 'purpose', 'review', 'secondary', 'select', 'sell', 'set', 'setting', 'specific', 'storage', 'tool', 'tracker', 'update', 'use', 'view'} #, 'window'}
all_pref_bigrams = {'ad choice', 'ad consent', 'adjust consent', 'adjust cookie', 'base ad', 'change consent', 'change cookie', 'change preference', 'change privacy', 'change setting', 'choose specific', 'configure consent', 'consent choice', 'consent detail', 'consent manager', 'consent modal', 'consent option', 'consent preference', 'consent tool', 'cookie ad', 'cookie choice', 'cookie consent', 'cookie learn', 'cookie policy', 'cookie preference', 'cookie sell', 'cookie set', 'cookie setting', 'customize cookie', 'customize setting', 'datum preference', 'detail modal', 'gdpr privacy', 'individual privacy', 'interest base', 'learn customize', 'let choose', 'manage cookie', 'manage datum', 'manage detail', 'manage option', 'manage preference', 'manage privacy', 'manage setting', 'manage tracker', 'manually manage', 'modal open', 'modal window', 'open consent', 'open cookie', 'open preference', 'personal information', 'personalize modal', 'preference modal', 'privacy configuration', 'privacy preference', 'privacy setting', 'review cookie', 'review option', 'select cookie', 'sell datum', 'sell personal', 'set cookie', 'set preference', 'setting adchoice', 'specific cookie', 'storage preference', 'tracker setting', 'update privacy', 'use cookie', 'view cookie', 'view option'}
pref_bigrams_likely = {'change consent', 'change setting', 'consent choice', 'consent tool', 'cookie consent', 'cookie preference', 'cookie setting', 'customize setting', 'manage cookie', 'review cookie'}


def num_tokens(text):
    return len(text.split()) if text is not None else 0

def num_tokens_more_than(text, k=9):
    return num_tokens(text) > k


def analyze_grams(train):
    pos_train = train[train.pref_btn]
    pref_grams = sorted([gram for grams in pos_train.inner_text_tokens for gram in grams])
    pref_grams.extend([gram for grams in pos_train.aria_label_tokens for gram in grams])
    pref_grams = sorted(list(set(pref_grams)), key=lambda text: (num_tokens(text), text))
    grams_1 = [gram for gram in pref_grams if num_tokens(gram) == 1]
    grams_2 = [gram for gram in pref_grams if num_tokens(gram) == 2]
    print('unigrams\n', grams_1)
    print('bigrams\n', grams_2)
    print('Non-included unigrams:', set(grams_1) - set(pref_unigrams))
    print('Non-included bigrams:', set(grams_2) - set(all_pref_bigrams))
    pref_bigrams = set(all_pref_bigrams) - set(pref_bigrams_likely)
    print(pref_bigrams)


def contain_pref_kw(grams):
    grams = set(grams)
    n_matches_1 = len(grams.intersection(pref_unigrams))
    n_matches_2 = len(grams.intersection(all_pref_bigrams))
    if len(grams.intersection(pref_bigrams_likely)) > 0:
        match_likely = 1
    else:
        match_likely = 0
    return n_matches_1, n_matches_2, match_likely


def contain_blacklist_kw(grams):
    for gram in grams:
        if gram in ['accept', 'deny']:
            return 1
    return 0


def contain_ccpa(text):
    phrases = ['do not sell my personal', 'california do not sell', 'do not sell my']
    if any(phrase.lower() in text.lower() for phrase in phrases):
        return 1
    return 0


def contain_signature_class(row):
    el_class = row['class']
    if el_class is None:
        return 0
    # consentomatic_list = ['app_gdpr', 'app_gdpr .popup_popup', 'app_gdpr--2k2uB', 'as-oil-content-overlay', 'banner_banner--3pjXd', 'cookie_banner_background', 'didomi-notice-banner', 'footer .evidon-footer-image', 'gdpr .switch span.on', 'js-consent-banner', 'message-container .message.type-modal', 'optanon-alert-box-wrapper', 'pdynamicbutton a', 'qc-cmp-ui-container', 'qc-cmp-ui-container.qc-cmp-showing', 'truste-consent-content', 'unic .unic-bar', 'unic .unic-box', 'wpgdprc-consent-bar']
    for claz in ['ot-sdk-show-settings', 'optanon-show-settings', 'optanon-toggle-display', 'css-1dhesuk', 'iubenda-advertising-preferences-link']:
        if claz in el_class:
            return 1
    return 0


def contain_signature_id(row):
    el_id = row['id']
    if el_id is None:
        return 0
    # consentomatic_list = ['CybotCookiebotDialogBody', 'CybotCookiebotDialogBodyButtonAccept', 'CybotCookiebotDialogBodyLevelButtonPreferences', '__tealiumGDPRecModal', '__tealiumGDPRecModal .privacy_prompt', '_evidon_banner', 'ac-Banner', 'ac-Banner._acc_visible', 'ccc-notify .ccc-notify-button', 'ccc[open]', 'cmpbox', 'cmpbox .cmpmore', 'coiOverlay', 'coiSummery', 'cookie-law-info-bar', 'cookieLab', 'didomi-host', 'didomi-notice', 'drcc-overlay', 'ez-cookie-dialog', 'mainMoreInfo', 'onetrust-banner-sdk', 'optanon-menu', 'optanon-popup-body-content', 'truste-consent-content']
    for aid in ['onetrust-pc-btn-handler', 'ot-sdk-btn', '#ot-sdk-btn-floating', 'teconsent', 'truste-show-consent' 'CybotCookiebotDialogBodyButtonDetails', '_evidon-link-text', 'adroll_consent_settings']:
        if aid in el_id:
            return 1
    return 0


def contain_signature_onclick(row):
    for click_func in ['Optanon.ToggleInfoDisplay()', 'googlefc.showRevocationMessage()', 'tC.privacyCenter.showPrivacyCenter()', 'Cookiebot.renew()']:
        for el in [row['onclick'], row['href']]:
            if el and click_func in el:
                return 1
    return 0


def tokenize(adf, localize=None, verbose=0):
    for col in ['inner_text', 'aria_label', 'title']:
        if verbose >= 2: print('tokenize', col)
        adf[f'{col}_tokens'] = adf[col].map(lambda col: tokenize_text(col, localize))  # note: use progress_map if needed.
    for col in ['id', 'class']:
        adf[f'{col}_tokens'] = adf[col].map(tokenize_classid)


def featurize_attr_df(adf, localize=None):
    """Featurizer a data frame containing attributes of buttons."""
    # feat = inner_text_vectorizer.transform(adf.inner_text_tokens).toarray()
    # len_feat = np.c_[adf.inner_text_tokens.map(len).to_list()]
    tokenize(adf, localize)
    feat_groups = [
            [np.c_[adf.inner_text_tokens.map(contain_pref_kw).to_list()],
             np.c_[adf.aria_label_tokens.map(contain_pref_kw).to_list()],
             np.c_[adf.id_tokens.map(contain_pref_kw).to_list()],
             np.c_[adf.class_tokens.map(contain_pref_kw).to_list()],
            ],
            # [np.c_[adf.inner_text_tokens.map(contain_blacklist_kw).to_list()],
            #  np.c_[adf.aria_label_tokens.map(contain_blacklist_kw).to_list()],
            # ],

            # [np.c_[adf.inner_text.map(num_tokens).to_list()],
            #  np.c_[adf.aria_label.map(num_tokens).to_list()],
            # ],

            [np.c_[adf.apply(contain_signature_id, axis=1).to_list()],
             np.c_[adf.apply(contain_signature_class, axis=1).to_list()],
             np.c_[adf.apply(contain_signature_onclick, axis=1).to_list()],
            ],

            [np.c_[adf.inner_text.map(num_tokens_more_than).to_list()],
             np.c_[adf.aria_label.map(num_tokens_more_than).to_list()],
            ]

            #  np.c_[adf.inner_text.map(contain_ccpa).to_list()],
    ]
    feat_group_arrays = [np.hstack(feat_group) for feat_group in feat_groups]
    feat_group_dims = [np.shape(feat_group_array)[1] for feat_group_array in feat_group_arrays]
    return np.hstack(feat_group_arrays), feat_group_dims

# %%
async def _notebook():
    # %%
    from io import BytesIO
    from IPython.display import display
    from PIL import Image

    from playwright.async_api import async_playwright
    import pandas as pd

    from consent.cmp.prefbtn.pref_btn_clf import PrefBtnClf
    from consent.cmp.prefbtn.pref_btn_identify import get_buttons, get_btn_attrs
    from ooutil.browser_async import goto_ignore_timeouterror

    import sys
    import importlib
    importlib.reload(sys.modules['consent.cmp.prefbtn.pref_btn_identify'])
    from consent.cmp.prefbtn.pref_btn_identify import get_buttons, get_btn_attrs

    # %%
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch()
    brcontext = None

    # %%
    if brcontext is not None:
        await brcontext.close()
    brcontext = await browser.new_context()
    # %%
    page = await brcontext.new_page()
    # url = "https://opendns.com/"
    url = "https://askubuntu.com/"

    # %%
    goto_ignore_timeouterror(page, url)
    display(Image.open(BytesIO(await page.screenshot())))

    # %%
    buttons = await get_buttons(page)
    btn_attrs = pd.DataFrame(await get_btn_attrs(buttons))
    assert len(btn_attrs) == len(buttons)
    btn_attrs
    # %%
    button_feat_df = featurize_attr_df(btn_attrs)
    preds = PrefBtnClf.get_clf().predict_proba(button_feat_df)
    found_btn_idx = np.argmax(preds[:,1])
    btn_attrs.iloc[found_btn_idx]

    # %%
    found_btn = btn_attrs.iloc[found_btn_idx]['el']
    # found_btn = buttons[found_btn_idx]
    await found_btn.text_content()

    # %%
    await found_btn.click()

    # %%
    display(Image.open(BytesIO(await page.screenshot())))

    # Get the button with the highest prediction probability.
    # return buttons[np.argmax(preds)]

    # %%
    preds = PrefBtnClf.get_clf().predict(button_feat_df)
    # %%
    for found_btn_idx in np.flatnonzero(preds):
        found_btn = btn_attrs['el'].iloc[found_btn_idx]
        print('btn is visible:', await found_btn.is_visible())

    # %%
    # %%
    await brcontext.close()
    brcontext = None

    # %%
    await browser.close()
    await playwright.stop()

    # %%

