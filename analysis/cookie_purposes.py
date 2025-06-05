import os, json
from cookiepedia import fetch_cookie_info, fetch_cookie_description, fetch_cookie_desc_csv


preference_dict = {}
if not os.path.exists('cookie_purposes.json'):
    cookie_data = {'NOHOST': {}, 'ALLHOSTS': {}}
else:
    with open('cookie_purposes.json', 'r') as f:
        cookie_data = json.load(f)
for root, dirs, files in os.walk('data/'):
    for file in files:
        site = root.split('/')[-1]
        if file == 'consent_resources.json':
            with open(os.path.join(root, file), 'r') as f:
                try:
                    resources = json.load(f)
                except json.decoder.JSONDecodeError:
                    continue
                preference_dict[site] = {'cookie_data': None, 'ui_data': None}
                if resources:
                    for resource in resources:
                        try:
                            preference_data = json.loads(resource['response'])
                        except json.decoder.JSONDecodeError:
                            temp_cookies = {}
                            for line in resource['response'].split('\n'):
                                if line.startswith('CookieConsentDialog.cookieTable'):
                                    if ' = [[' in line:
                                        category = line.split(' = [[')[0].split('CookieConsentDialog.cookieTable')[1]
                                        resources = json.loads('[[' + line.split(' = [[')[1].strip()[:-1])
                                        temp_cookies[category] = resources
                            for category, cookies in temp_cookies.items():
                                for cookie in cookies:
                                    if cookie[0] in cookie_data['ALLHOSTS']:
                                        continue
                                    if len(cookie[2]) > 3:
                                        description = cookie[2]
                                    else:
                                        description = fetch_cookie_desc_csv(cookie[0])
                                        if not description:
                                            description = fetch_cookie_description(cookie[0])
                                    if cookie[1] not in cookie_data:
                                        cookie_data[cookie[1]] = {}
                                    if cookie[0] not in cookie_data[cookie[1]]:
                                        cookie_data[cookie[1]][cookie[0]] = {'Name': cookie[0], 'Host': cookie[1], 'Description': description}
                                    elif cookie[0] not in cookie_data['NOHOST']:
                                        cookie_data['NOHOST'][cookie[0]] = {'Name': cookie[0], 'Host': cookie[1], 'Description': description}
                                    if cookie[0] not in cookie_data['ALLHOSTS']:
                                        cookie_data['ALLHOSTS'][cookie[0]] = {'Name': cookie[0], 'Host': cookie[1], 'Description': description}
                                    with open('cookie_purposes.json', 'w') as f:
                                        json.dump(cookie_data, f, indent=4)
                            continue
                        if 'DomainData' not in preference_data:
                            continue
                        # preference_dict[site]['cookie_data'] = preference_data['DomainData']
                        # preference_dict[site]['ui_data'] = preference_data['NtfyConfig']
                        for cookie_groups in preference_data['DomainData']['Groups']:
                            for cookie in cookie_groups['FirstPartyCookies']:
                                if cookie['Name'] in cookie_data['ALLHOSTS']:
                                    continue
                                if cookie['Host']:
                                    if len(cookie['description']) > 3:
                                        description = cookie['description']
                                    else:
                                        description = fetch_cookie_desc_csv(cookie['Name'])
                                        if not description:
                                            description = fetch_cookie_description(cookie['Name'])
                                    if cookie['Host'] not in cookie_data:
                                        cookie_data[cookie['Host']] = {}
                                    if cookie['Name'] not in cookie_data[cookie['Host']]:
                                        cookie_data[cookie['Host']][cookie['Name']] = {'Name': cookie['Name'], 'Host': cookie['Host'], 'Description': description}
                                    elif len(cookie['description']) > 3:
                                        cookie_data[cookie['Host']][cookie['Name']]['Description'] = description
                                elif cookie['Name'] not in cookie_data['NOHOST']:
                                    cookie_data['NOHOST'][cookie['Name']] = {'Name': cookie['Name'], 'Host': cookie['Host'], 'Description': description}
                                if cookie['Name'] not in cookie_data['ALLHOSTS']:
                                    cookie_data['ALLHOSTS'][cookie['Name']] = {'Name': cookie['Name'], 'Host': cookie['Host'], 'Description': description}
                                with open('cookie_purposes.json', 'w') as f:
                                    json.dump(cookie_data, f, indent=4)

with open('cookie_purposes.json', 'r') as f:
    cur_cookie_data = json.load(f)
    for root, dirs, files in os.walk('data/'):
        for file in files:
            if file == 'postrej_browser_cookies.json' or file == 'prerej_cookies.json':
                with open(os.path.join(root, file), 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies['browser_cookies']:
                        cookie_name = cookie['name']
                        if cookie['name'] in cur_cookie_data['ALLHOSTS']:
                            continue
                        if cookie['domain'] in cur_cookie_data:
                            if cookie_name not in cur_cookie_data[cookie['domain']]:
                                description = fetch_cookie_desc_csv(cookie['name'])
                                if not description:
                                    description = fetch_cookie_description(cookie['name'])
                                cur_cookie_data[cookie['domain']][cookie_name] = {'Name': cookie_name, 'Description': description}
                                cur_cookie_data['ALLHOSTS'][cookie_name] = {'Name': cookie_name, 'Description': description}
                        else:
                            found = False
                            for cur_host, cur_cookies in cur_cookie_data.items():
                                if cookie_name in cur_cookies:
                                    found = True
                            if not found:
                                description = fetch_cookie_desc_csv(cookie['name'])
                                if not description:
                                    description = fetch_cookie_description(cookie['name'])
                                cur_cookie_data[cookie['domain']] = {}
                                cur_cookie_data[cur_host][cookie_name] = {'Name': cookie_name, 'Description': description}
                                cur_cookie_data['ALLHOSTS'][cookie_name] = {'Name': cookie_name, 'Description': description}
                        with open('cookie_purposes.json', 'w') as f:
                            json.dump(cur_cookie_data, f, indent=4)
