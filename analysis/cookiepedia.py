from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd


database_csv = {'category': [], 'name': [], 'domain': [], 'description': []}
df = pd.read_csv('open-cookie-database.csv')
for row in df.iterrows():
    database_csv['category'].append(row[1]['Category'])
    database_csv['name'].append(row[1]['Cookie / Data Key name'])
    database_csv['domain'].append(row[1]['Domain'])
    database_csv['description'].append(row[1]['Description'])


def fetch_cookie_description(cookie_name):
    try:
        url = 'https://cookiepedia.co.uk/'
        with sync_playwright() as p:
            browser = p.firefox.launch(channel="firefox", headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state('domcontentloaded')
            page.click('button[id="onetrust-reject-all-handler"]')
            page.select_option('select#search-type', 'cookie')
            page.fill('input#search-query', cookie_name)
            page.click('input[type="submit"][value="Search"]')
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_load_state('networkidle')
            html = page.content()
            browser.close()
    
        soup = BeautifulSoup(html, 'html.parser')
        content_left = soup.find('div', id='content-left')
        if not content_left:
            print("Cookie information not found.")
            return
        about_h2 = content_left.find('h2', text='About this cookie:')
        if about_h2:
            description_p = about_h2.find_next_sibling('p')
            if description_p:
                description = description_p.get_text(strip=True)
            else:
                description = "Description not found."
        else:
            description = "Description not found."
        if 'The main purpose of this cookie is' in content_left.get_text():
            purpose = content_left.get_text().split('The main purpose of this cookie is:')[1].split('Key numbers')[0].strip()
        else:
            purpose = "Purpose not found."
        print(f"\nDescription: {description}\nPurpose: {purpose}")
    except Exception as e:
        print(f"Error: {e}")
        return

def fetch_cookie_info(website):
    url = f'https://cookiepedia.co.uk/website/{website}'
    with sync_playwright() as p:
        # Launch Firefox Nightly
        browser = p.firefox.launch(channel="firefox", headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('domcontentloaded')
        html = page.content()
        browser.close()
    soup = BeautifulSoup(html, 'html.parser')
    ul_elements = soup.find_all('ul', class_='margin-bottom')
    cookies = []
    for ul_element in ul_elements:
        for li in ul_element.find_all('li', recursive=False):
            cookie_info = {}
            # Get cookie name
            cookie_name_strong = li.find('strong', text='Cookie name:')
            if not cookie_name_strong:
                continue
            cookie_name_a = cookie_name_strong.find_next('a')
            if not cookie_name_a:
                continue
            cookie_name = cookie_name_a.text.strip()
            cookie_info['Cookie name'] = cookie_name
            # Now extract other details
            details_uls = li.find_all('ul', class_='cookie-details clearfix')
            for details_ul in details_uls:
                for detail_li in details_ul.find_all('li'):
                    strong_tag = detail_li.find('strong')
                    if strong_tag:
                        key = strong_tag.text.strip().strip(':')
                        if key == 'About this Cookie':
                            span_tag = detail_li.find('span')
                            if span_tag:
                                value = span_tag.get_text(strip=True)
                            else:
                                value = detail_li.get_text(separator=' ', strip=True).replace(strong_tag.text, '', 1).strip()
                        else:
                            # Get text after the strong tag
                            text = detail_li.get_text(separator=' ', strip=True)
                            value = text.replace(strong_tag.text, '', 1).strip(':').strip()
                        cookie_info[key] = value
            cookies.append(cookie_info)
    return cookies


def fetch_cookie_desc_csv(cookie_name):
    for i, name in enumerate(database_csv['name']):
        if cookie_name == name:
            return database_csv['description'][i]
    return False


def main(website):
    cookies = fetch_cookie_info(website)
    if cookies:
        for idx, cookie in enumerate(cookies, 1):
            print(f"\nCookie {idx}:")
            for key, value in cookie.items():
                print(f"{key}: {value}")
    else:
        print("No cookie information found.")


if __name__ == '__main__':
    cookie_name = input("Enter the cookie name (e.g., '__gads'): ")
    fetch_cookie_description(cookie_name)
    websites = []
    for website in websites:
        main(website)
