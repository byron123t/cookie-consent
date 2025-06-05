import re, os, base64, json
import pandas as pd
import pyarrow.parquet as pq
from tqdm import tqdm
from zxcvbn import zxcvbn
import numpy as np


with open('data/cookie_purposes.json') as f:
    cookie_purposes = json.load(f)


def contains_personal_information(cookie):
    # tracker_keywords = ['tracker', 'track', 'trck', 'identifier', '_uid', '_id', '_gid,', '_uuid', 'user_id', 'session_id', 'sess_id', 'sess_uid', 'usr_id', '_gads', '_ga', '_gat', '_gid', '_gaexp', 'google-analytics', 'google_analytics', 'googleanalytics', 'fbp', 'fbclid', 'fbid', 'fbcid', 'fbm_', 'fbclid_', 'fbp_', 'fbm_', '_fbp', '_fbc', 'adid', 'device_id', 'ifa', 'ad_identifier', 'advertising id', 'advertising_id', 'advertisingid', 'ad_id', 'deviceid', 'device_id', 'device-id', 'deviceid_', 'device-id_', '_deviceid', '_device-id', '_deviceid_', '_device-id_', '_adid', '_ad_id', 'analytics_', 'advertising_']
    tracker_keywords = ['tracker', 'track', 'trck', 'identifier', '_uid', '_id', '-id', '_gid,', '_uuid', 'user_id', 'session_id', 'sess_id', 'sess_uid', 'usr_id', '_gads', '_ga', '_gat', '_gid', '_gaexp', 'google-analytics', 'google_analytics', 'googleanalytics', 'fbp', 'fbclid', 'fbid', 'fbcid', 'fbm_', 'fbclid_', 'fbp_', 'fbm_', '_fbp', '_fbc', 'adid', 'device_id', 'ifa', 'ad_identifier', 'advertising id', 'advertising_id', 'advertisingid', 'ad_id', 'deviceid', 'device_id', 'device-id', 'deviceid_', 'device-id_', '_deviceid', '_device-id', '_deviceid_', '_device-id_', '_adid', '_ad_id', 'analytics_', 'advertising_', 'session']
    # location_keywords = ['location', 'latitude', 'longitude', 'city', 'country', 'postal', 'address', 'geoloc', '_loc', '_geo', 'united-kingdom', 'united kingdom', 'united_kingdom', 'california', 'united states', 'united-states', 'united_states', 'germany', 'great-britain', 'great_britain', 'great britain', 'ec2n 3ar', '60323', '95051', 'santa clara', 'santa-clara', 'santa_clara', 'london', 'frankfurt', 'south africa', 'south-africa', 'south_africa', 'australia', 'singapore', 'canada', 'ireland', 'michigan', 'capetown', 'sydney', 'toronto', 'san francisco', 'san-francisco', 'san_francisco', 'eu', 'uk', 'au', 'sg', 'ca', 'za', 'can', 'us', 'usa']
    location_keywords = ['location', 'latitude', 'longitude', 'city', 'country', 'postal', 'address', 'geoloc', '_loc', '_geo', 'united-kingdom', 'united kingdom', 'united_kingdom', 'california', 'united states', 'united-states', 'united_states', 'germany', 'great-britain', 'great_britain', 'great britain', 'ec2n 3ar', '60323', '95051', 'santa clara', 'santa-clara', 'santa_clara', 'london', 'frankfurt', 'south africa', 'south-africa', 'south_africa', 'australia', 'singapore', 'canada', 'ireland', 'michigan', 'capetown', 'sydney', 'toronto', 'san francisco', 'san-francisco', 'san_francisco', 'region', 'locale', 'timezone']
    ip_address_keywords = ['ip_address', 'ip-address', '_ip', '-ip', 'ip address']
    # demographic_keywords = ['gender', 'income', 'demographic', 'ethnicity', 'age', 'first_name', 'last_name', 'full_name', 'dob', 'birthdate']
    demographic_keywords = ['gender', 'income', 'demographic', 'ethnicity', 'first_name', 'last_name', 'full_name', 'birthdate']
    language_keywords = ['language', 'lang']
    tracker_patterns = [
        r'(?i)utm_[a-z]+',  # UTM parameters
        r'[a-fA-F0-9]{8}(-|\.)([a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}', # UUID
        r'^GA\d\.\d\.\d+\.\d+$', # Google Analytics ID
        r'^fb\d\.\d\.\d+\.\d+$', # Facebook Pixel ID
        r'\b(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}\b' # MAC address
    ]
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    phone_pattern = r'\+?\d{1,3}[ -]?\(?\d{1,4}\)?[ -]?\d{1,4}[ -]?\d{1,9}'
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    location_patterns = [
        r'-?(\d+\.\d+),\s*-?(\d+\.\d+)',       # lat,long
        r'\b\d{5}(?:-\d{4})?\b',               # US ZIP (e.g. 12345 or 12345-6789)
    ]

    ip_address_patterns = [
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',        # IPv4
        r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b',  # IPv6
    ]
    # print(cookie[0], cookie[1])
    for i, column in enumerate(cookie):
        if any(keyword in str(column).lower() for keyword in tracker_keywords):
            # print('tracker')
            return 'tracker'
        if any(keyword in str(column).lower() for keyword in location_keywords):
            # print('location')
            return 'location'
        if any(keyword in str(column).lower() for keyword in ip_address_keywords):
            # print('ip_address')
            return 'ip_address'
        if any(keyword in str(column).lower() for keyword in language_keywords):
            # print('language')
            return 'language'

        if any(re.search(pattern, str(column)) for pattern in tracker_patterns):
            # print('tracker')
            return 'tracker'
        if any(re.search(pattern, str(column)) for pattern in location_patterns):
            # print('location')
            return 'location'
        if any(re.search(pattern, str(column)) for pattern in ip_address_patterns):
            # print('ip_address')
            return 'ip_address'
        if any(re.search(pattern, str(column)) for pattern in language_keywords):
            # print('language')
            return 'language'

        try:
            decoded_string = base64.b64decode(str(column)).decode('utf-8')
            if any(keyword in decoded_string.lower() for keyword in tracker_keywords):
                # print('tracker')
                return 'tracker'
            if any(keyword in decoded_string.lower() for keyword in location_keywords):
                # print('location')
                return 'location'
            if any(keyword in decoded_string.lower() for keyword in ip_address_keywords):
                # print('ip_address')
                return 'ip_address'
            if any(keyword in decoded_string.lower() for keyword in language_keywords):
                # print('language')
                return 'language'

            if any(re.search(pattern, decoded_string) for pattern in tracker_patterns):
                # print('tracker')
                return 'tracker'
            if any(re.search(pattern, str(column)) for pattern in location_patterns):
                # print('location')
                return 'location'
            if any(re.search(pattern, str(column)) for pattern in ip_address_patterns):
                # print('ip_address')
                return 'ip_address'
            if any(re.search(pattern, str(column)) for pattern in language_keywords):
                # print('language')
                return 'language'

        except Exception as e:
            pass

        if i == 0 and column in cookie_purposes['ALLHOSTS']:
            description = cookie_purposes['ALLHOSTS'][column]['Description']
            if description:
                if any(keyword in description.lower() for keyword in tracker_keywords):
                    # print('tracker')
                    return 'tracker'
                if any(keyword in description.lower() for keyword in location_keywords):
                    # print('location')
                    return 'location'
                if any(keyword in description.lower() for keyword in ip_address_keywords):
                    # print('ip_address')
                    return 'ip_address'
                if any(keyword in description.lower() for keyword in language_keywords):
                    # print('language')
                    return 'language'
    
    try:
        if len(cookie[1]) < 72:
            zxcvbn_score = zxcvbn(str(cookie[1]))['guesses_log10']
            # print('zxcvbn guesses_log10:', zxcvbn_score)
            if zxcvbn_score > 10:
                # print('tracker')
                return 'tracker'
    except Exception as e:
        pass
    # print(cookie[0], cookie[1], 'False')
    return 'False'


out_data = {}
for region in ['ca', 'eu', 'uk', 'au', 'us', 'sg', 'can', 'za']:
    out_data[region] = {'trackers': 0, 'location': 0, 'ip_address': 0, 'language': 0, 'False': 0}
    for iteration in tqdm(range(0, 10)):
        for mode in ['0k_20k']:
            df1 = pq.read_table('data/regions/{}/all_complies_{}_{}.parquet'.format(region, mode, iteration)).to_pandas()
            df2 = pq.read_table('data/regions/{}/scan_{}_{}.parquet'.format(region, mode, iteration)).to_pandas()
            df2 = df2.reset_index(drop=True)
            df2 = df2.drop_duplicates(subset=['name', 'domain', 'site'])
            df2 = df2.drop(['path', 'expires', 'size', 'httpOnly', 'secure', 'session', 'sameSite', 'priority', 'sameParty', 'sourceScheme', 'sourcePort', 'request_url', 'page_url'], axis=1)

            df2 = df2.merge(
                df1[['name', 'domain', 'site', 'comply']],
                on=['name', 'domain', 'site'],
                how='left'
            )
            
            # for index, row in tqdm(df1.iterrows(), total=len(df1)):
            #     criteria = (row['name'] == df2['name']) & (row['domain'] == df2['domain']) & (row['site'] == df2['site'])
            #     df2.loc[criteria, 'comply'] = row['comply']
            
            df2['contains_personal_info'] = df2.apply(contains_personal_information, axis=1)
            # print proportion of cookies containing personal information
            print('Proportion of cookies containing personal information: {:.2f}%'.format(df2['contains_personal_info'].value_counts(normalize=True).get('tracker', 0) * 100))
            print('Proportion of cookies containing personal information: {:.2f}%'.format(df2['contains_personal_info'].value_counts(normalize=True).get('location', 0) * 100))
            print('Proportion of cookies containing personal information: {:.2f}%'.format(df2['contains_personal_info'].value_counts(normalize=True).get('ip_address', 0) * 100))
            print('Proportion of cookies containing personal information: {:.2f}%'.format(df2['contains_personal_info'].value_counts(normalize=True).get('language', 0) * 100))
            print('Proportion of cookies NOT containing personal information: {:.2f}%'.format(df2['contains_personal_info'].value_counts(normalize=True).get('False', 0) * 100))
            
            out_data[region]['trackers'] += df2['contains_personal_info'].value_counts(normalize=True).get('tracker', 0) * 100
            out_data[region]['location'] += df2['contains_personal_info'].value_counts(normalize=True).get('location', 0) * 100
            out_data[region]['ip_address'] += df2['contains_personal_info'].value_counts(normalize=True).get('ip_address', 0) * 100
            out_data[region]['language'] += df2['contains_personal_info'].value_counts(normalize=True).get('language', 0) * 100
            out_data[region]['False'] += df2['contains_personal_info'].value_counts(normalize=True).get('False', 0) * 100

            df2.to_parquet('data/regions/{}/scan_{}_comply_{}.parquet'.format(region, mode, iteration))
    out_data[region]['trackers'] /= 10
    out_data[region]['location'] /= 10
    out_data[region]['ip_address'] /= 10
    out_data[region]['language'] /= 10
    out_data[region]['False'] /= 10
    with open('data/out_personal_info_data.json'.format(region), 'w') as f:
        json.dump(out_data, f, indent=4)
