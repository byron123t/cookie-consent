# %%
import asyncio
from pathlib import Path
import tempfile

from colorama import Fore

from consent.cmp.prefbtn.pref_btn_identify import get_and_save_pref_btn_df_on_page
from consent.data.cookie_setting import CookieSetting
from consent.data.database.exper_result_database import ExperResultDatabase
from consent.data.banner_anno import BannerDataset
from consent.data.cookie_setting import CookieSetting
from consent.util.default_path import create_data_dir, get_data_dir
from ooutil.browser_factory import get_page
from ooutil.df_util import find_one

from consent.cmp.prefbtn.pref_btn_identify import get_and_save_pref_btn_df_on_page
import sys; import importlib; importlib.reload(sys.modules['consent.cmp.prefbtn.pref_btn_identify'])
from consent.cmp.prefbtn.pref_btn_identify import get_and_save_pref_btn_df_on_page

def get_home_page_load(hpl, url):
    return find_one(hpl, 'url', url)

def get_home_page_load_by_site(hpl, site):
    return find_one(hpl, 'site', site)

async def save_pref_btn_df_on_page(site, pref_btn_sels, html, out_dir, frame_i, java_script_enabled):
    out_file = out_dir / (f'{site}_{frame_i}.csv')

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html') as tmp_file:
        tmp_file.write(html)
        tmp_file.flush()
        # Disable JS as we use Chrome just for parsing the HTML
        async with get_page(stealth_mode=False, java_script_enabled=java_script_enabled) as page:
            # await goto_ignore_timeout_error(page, )
            url = 'file://' + tmp_file.name
            return await get_and_save_pref_btn_df_on_page(None, page, url, pref_btn_sels, site, out_file=out_file)

def get_selectors(opt_settings):
    for opt_setting in opt_settings:
        assert 'pref_btn' in opt_setting, f'{opt_setting=} contains no pref btn'
        yield opt_setting['pref_btn']

async def create_dataset(anno_sites, hpl, out_dir, verbose=2):
    error_sites = []
    for row in anno_sites.itertuples():
        asite = row.site
        assert '_' not in asite, f'{asite} should not have _ in name, which we use as a delimiter for frames'

        print(f"{Fore.GREEN}Process site {asite}", Fore.RESET)
        if verbose >= 2: print(row.opt_page)
        # page_load = get_home_page_load(hpl, row.opt_page) # asite)
        page_load = get_home_page_load_by_site(hpl, asite)
        # assert page_load is not None, f'Home page load of {asite} not found'
        if page_load is None:
            print(f'{Fore.RED} ERROR: Home page load of {asite} not found {Fore.RESET}')
            continue

        selectors = list(get_selectors(row.opt_setting))

        n_found = 0
        try:
            for i, frame in enumerate(page_load['frames']):
                html = frame['content']
                n_found_frame = await save_pref_btn_df_on_page(asite, selectors, html, out_dir, i, java_script_enabled=False)
                if n_found_frame == 0:
                    print("Frame not found, retry with JS enabled")
                    n_found_frame = await save_pref_btn_df_on_page(asite, selectors, html, out_dir, i, java_script_enabled=True)

                if n_found_frame:
                    print('Found pref btn')
                    n_found += n_found_frame
                    if n_found == len(selectors):  # found all pref btns
                        break
        except Exception as e:
            error_sites.append((asite, e))
            raise e  # Verbose for debugging
    print("Error sites:")
    print(error_sites)


def filter_done_sites(anno_sites, out_dir, verbose=0):
    done_sites = []
    for site in anno_sites.site:
        if len(list(out_dir.glob(f'{site}*.csv'))) > 0:
            if verbose >= 2: print(f"Skip, result file exist for {site}")
            done_sites.append(site)
    return anno_sites[~anno_sites.site.isin(done_sites)]

# TODO: remove this duplicate function with eu_create_pref_btn_dataset.
def replace_with_manual_crawl(hpl, crawl_dir, verbose=2):
    def shorten_dir_path(apath: str):
        prefix = str(crawl_dir) + '/'
        assert apath.startswith(prefix), f'apath should starts with {prefix}'
        return apath[len(prefix):]
    site_to_frames = {}
    for site_dir in crawl_dir.glob('*'):
        site = site_dir.name
        frames = []
        html_files = []
        for html_file in site_dir.glob('**/*.html'):
            html_files.append(html_file)
            if verbose >= 3: print(f'Read {html_file}')
            frames.append({'url': shorten_dir_path(str(html_file)), 'content': html_file.read_text()})
        site_to_frames[site] = frames
        if verbose >= 3: print(f"Replace {site} -> {[shorten_dir_path(str(html_file)) for html_file in html_files]}")

    hpl['frames'] = hpl.apply(lambda row: site_to_frames.get(row['site'], row['frames']), axis=1)

async def main():
    # manual_crawl_date, crawl_date, cookie_setting_file = '2022-05-24', '2021-07-28', Path('/home/ducbui/Dropbox/projects/consent/consent_project/src/consent/data/cookie_setting.yml')
    manual_crawl_date, crawl_date, cookie_setting_file = '2022-05-26', '2022-05-26', Path('/home/ducbui/Dropbox/projects/consent/consent_project/src/consent/data/cookie_setting_eu2.yml')

    manual_crawl_dir = get_data_dir(f'{manual_crawl_date}/pref_btn_dataset_html')
    # manual_crawl_dir = get_data_dir(f'{manual_crawl_date}/new')  # development

    interest_sites = None # [adir.name for adir in manual_crawl_dir.glob('*')]
    # interest_sites = ['proquest.com', 'churchofjesuschrist.org', 'wunderground.com', 'mattel.com', 'zimbra.com']
    interest_sites = ['wrike.com']  #['samsungelectronics.com', 'sendgrid.com', 'wrike.com', 'xiaomi.com']

    anno_sites = CookieSetting.get_cookie_settings(nocache=True, pref_btn_only=True, cookie_setting_files=[cookie_setting_file])

    # Remove no-opt-setting sites.
    anno_sites = anno_sites[anno_sites.pref_buttons.map(lambda btns: len(btns) > 0)]
    print('Annotated sites:', len(anno_sites), '\n', anno_sites)
    if len(anno_sites) == 0:
        print("Nothing to do")
        return

    if interest_sites: anno_sites = anno_sites[anno_sites.site.isin(interest_sites)]
    hpl = ExperResultDatabase(crawl_date, 'home_page_load_result').query_to_df(query={'site': {'$in': anno_sites.site.tolist()}}, projection=['site', 'frames', 'url'])

    hpl = hpl.drop_duplicates(subset=['site'], keep='last')
    replace_with_manual_crawl(hpl, manual_crawl_dir)
    print(hpl)
    print('Num unique sites:', hpl.site.nunique())

    out_exper_date = manual_crawl_date  # 2021-08-04 2021-11-26
    out_dir = create_data_dir(f'{out_exper_date}/pref_btn')
    # Uncomment if want to overwrite.
    # anno_sites = filter_done_sites(anno_sites, out_dir)

    await create_dataset(anno_sites, hpl, out_dir)

if __name__ == '__main__':
    asyncio.run(main())
    # await main()
# %%
