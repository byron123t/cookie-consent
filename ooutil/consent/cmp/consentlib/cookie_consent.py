from typing import Optional


class CategoryConsent(dict):
    def __init__(self, category: Optional[str], category_id: Optional[str], prev_status: Optional[bool], cur_status: bool): # , cookie_list: List):
        self['category']  = category
        self['category_id']  = category_id
        self['prev_status'] = prev_status
        self['cur_status'] = cur_status


class CookieConsent(dict):
    def __setitem__(self, category, category_consent: CategoryConsent):
        assert isinstance(category_consent, CategoryConsent), f'Invalid {type(category_consent)=}'
        super().__setitem__(category, category_consent)
