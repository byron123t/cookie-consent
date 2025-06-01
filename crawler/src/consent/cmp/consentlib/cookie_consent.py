from typing import Dict, NamedTuple, List, Optional, Any
import json


# class CategoryConsent: # (NamedTuple):
#     def __init__(self, category, category_id, prev_status, cur_status, cookie_list):
#         self.category: Optional[str] = category
#         self.category_id: Optional[str] =category_id
#         self.prev_status: Optional[bool] = prev_status
#         self.cur_status: Optional[bool] = cur_status
#         self.cookie_list: List = cookie_list
#         # 'name': extract_cookie_category_name(), # may be uncessary

#     def __str__(self) -> str:
#         return str(self.__dict__)

class CategoryConsent(dict): # (NamedTuple):
    def __init__(self, category: Optional[str], category_id: Optional[str], prev_status: Optional[bool], cur_status: bool): # , cookie_list: List):
        self['category']  = category
        self['category_id']  = category_id
        self['prev_status'] = prev_status
        self['cur_status'] = cur_status
        # self['cookie_list'] = cookie_list # for analyze UI?
        # 'name': extract_cookie_category_name(), # may be uncessary



class CookieConsent(dict):
    def __setitem__(self, category, category_consent: CategoryConsent):
        assert isinstance(category_consent, CategoryConsent), f'Invalid {type(category_consent)=}'
        super().__setitem__(category, category_consent)


def test_serializable():
    cookie_consent = CookieConsent()
    cat_consent = CategoryConsent('necessary', 'necessary', True, True, [])
    cookie_consent['necessary'] = cat_consent

    print(json.dumps(cookie_consent)) # , default=lambda x: x.__dict__))
    print(f'{str(cat_consent)=}')


if __name__ == '__main__':
    test_serializable()
