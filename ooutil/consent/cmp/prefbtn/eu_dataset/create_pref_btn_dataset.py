# %%
from pathlib import Path
import asyncio

from bs4 import BeautifulSoup

from consent.util.default_path import create_data_dir, get_data_dir
from consent.data.eu_cookie_setting import EuCookieSetting
from consent.data.database.exper_result_database import ExperResultDatabase
from consent.cmp.prefbtn.dataset.create_pref_btn_dataset import create_dataset, filter_done_sites


def dev():
    site_html_dir = get_data_dir('2021-11-17') / 'pref_btn_eu_html'
    # Get pref btn
    # TODO: change to use a yaml file.
    site_to_pref_btn_selector = {
        'advangelists.com': '#text-2 > div > p > a',
        'news.com.au': 'body > footer > div.footer_inner > div > div.footer_notes.g_font-base-s > ul > li.footer_external-links_opt-out > a'}

    for site in site_html_dir.glob('*'):
        print('Site:', site.name)
        for html_file in site.glob('**/*.html'):
            selector = site_to_pref_btn_selector[site.name]
            html = html_file.read_text()
            soup = BeautifulSoup(html, features='lxml')
            pref_btns = soup.select(selector)
            if len(pref_btns) > 0:
                print(html_file)
                print(pref_btns)
    csets = EuCookieSetting.get_cookie_settings()
    asite = csets.iloc[0]
    site_db = ExperResultDatabase(
        '2021-11-17', 'home_page_load_result').query_to_df({'url': asite['opt_page'], 'location': 'eu'})
    selector = asite['opt_setting'][0]['pref_btn']
    asite_db = site_db.iloc[0]
    for frame in asite_db['frames']:
        soup = BeautifulSoup(frame['content'], features='lxml')
        pref_btns = soup.select(selector)
        if len(pref_btns) > 0:
            print(pref_btns)

def replace_with_manual_crawl(hpl, crawl_dir):
    def shorten_dir_path(apath: str):
        prefix = str(crawl_dir) + '/'
        assert apath.startswith(prefix), f'apath should starts with {prefix}'
        return apath[len(prefix):]
    site_to_frames = {}
    for site_dir in crawl_dir.glob('*'):
        site = site_dir.name
        frames = []
        for html_file in site_dir.glob('**/*.html'):
            frames.append({'url': shorten_dir_path(str(html_file)), 'content': html_file.read_text()})
        site_to_frames[site] = frames

    hpl['frames'] = hpl.apply(lambda row: site_to_frames.get(row['site'], row['frames']), axis=1)

async def main():
    interest_sites = None

    anno_sites = EuCookieSetting.get_cookie_settings(
        nocache=True, pref_btn_only=True)
    if interest_sites:
        anno_sites = anno_sites[anno_sites.site.isin(interest_sites)]

    hpl = ExperResultDatabase('2021-11-17', 'home_page_load_result').query_to_df(
        query={'site': {'$in': anno_sites.site.tolist()}, 'location': 'eu'},
               projection=['site', 'frames', 'url'])

    manual_crawl_dir = get_data_dir('2021-11-17/pref_btn_eu_html')
    replace_with_manual_crawl(hpl, manual_crawl_dir)
    print(hpl[hpl.site == 'geni.us'])

    out_dir = create_data_dir('2021-11-19/pref_btn')
    print(f'Out dir: {out_dir}')
    # Always overwrite...
    # anno_sites = list(filter_done_sites(anno_sites, out_dir))
    await create_dataset(anno_sites, hpl, out_dir)

if __name__ == '__main__':
    asyncio.run(main())