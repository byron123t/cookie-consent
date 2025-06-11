import json
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations


plt.rcParams.update({'pdf.fonttype': 42})
plt.rcParams.update({'ps.fonttype': 42})
plt.rcParams.update({'font.size': 16})

with open('data/cmp_ui_data.json') as f:
    data = json.load(f)

regions = list(data.keys())

websites_per_region = {region: set(data[region].keys()) for region in regions}
websites_in_all_regions = set.intersection(*websites_per_region.values())
print(len(websites_in_all_regions), 'websites are present in all regions.')

# Initialize a list to store the data
records = []

# Transform the nested JSON into a flat structure
for region, region_data in data.items():
    for website, website_data in region_data.items():
        if website in websites_in_all_regions:
            for ui_key, ui_value in website_data.items():
                records.append({
                    'region': region.upper(),
                    'website': website,
                    'ui_key': ui_key,
                    'ui_value': ui_value
                })

# Create a DataFrame
df = pd.DataFrame(records)

# Step 2: Pivot the DataFrame to get regions as columns
pivot_df = df.pivot_table(index=['website', 'ui_key'], columns='region', values='ui_value', aggfunc='first').reset_index()

# Update regions list in case any regions are missing after filtering
regions = df['region'].unique().tolist()

# Step 3: Analyze differences

# Function to count differences between regions for each ui_key
def count_differences(row):
    values = row[regions].tolist()
    newvalues = []
    for value in values:
        if str(value) not in newvalues:
            if isinstance(value, list):
                newvalues.append(str(value[0]).strip())
            else:
                newvalues.append(str(value).strip())
    unique_values = set(newvalues)
    return len(unique_values) - 1  # Subtract 1 because if all values are same, len(unique_values) == 1

pivot_df['diff_count'] = pivot_df.apply(count_differences, axis=1)
colors = plt.cm.Set3(np.linspace(0, 1, len(regions)))

# Step 4: Plot normalized stacked histograms for each UI setting key
for ui_key in pivot_df['ui_key'].unique():
    try:
        subset = pivot_df[pivot_df['ui_key'] == ui_key]
        melted = subset.melt(id_vars=['website', 'ui_key'], value_vars=regions, var_name='region', value_name='ui_value')

        counts = melted.groupby(['ui_value', 'region']).size().reset_index(name='count')

        total_counts = counts.groupby('ui_value')['count'].sum().reset_index(name='total_count')

        # Merge total_counts back into counts
        counts = counts.merge(total_counts, on='ui_value')

        if ui_key in ['AboutCookiesText', 'BannerShowRejectAllButton', 'ChoicesBanner', 'ConfirmText', 'ConsentModel']:
            counts = counts[counts['total_count'] >= 10]
        elif ui_key in ['AboutLink', 'AboutText', 'AlertAllowCookiesText', 'AlertMoreInfoText', 'AlertNoticeText', 'CookieSettingButtonText', 'MainInfoText', 'MainText']:
            counts = counts[counts['total_count'] >= 30]
        elif ui_key in ['about', 'AcceptAllCookies', 'AllowAllText', 'CloseShouldAcceptAllCookies', 'CookiesDescText', 'cookiesOverviewText', 'cookieTableHeaderExpiry', 'cookieTableHeaderName', 'cookieTableHeaderProvider', 'cookieTableHeaderPurpose', 'cookieTableHeaderType', 'ConsentSelection', 'consentTitle', 'cookiesOverviewText', 'details', 'domainConsent', 'domainConsentList', 'externalLinkIconAltText', 'lastUpdatedText', 'logoAltText', 'mandatoryText', 'noCookiesTypeText', 'opensInNewWindowText', 'privacyPolicyText', 'promotionBannerEnabled', 'providerLinkText', 'userCulture', 'userCountry', 'ucDataShieldPromotionBannerTitle', 'ucDataShieldPromotionBannerCTA', 'ucDataShieldPromotionBannerBody']:
            continue
        else:
            counts = counts[counts['total_count'] >= 10]

        # Filter out 'ui_value's with total counts less than 10

        # If there are no 'ui_value's with total counts >= 10, skip plotting
        if counts.empty:
            continue

        # Compute proportions
        counts['proportion'] = counts['count'] / counts['total_count']

        # Pivot the data to have 'ui_value' as index and regions as columns
        pivot_counts = counts.pivot(index='ui_value', columns='region', values='proportion').fillna(0)

        # Sort ui_values for consistent plotting
        pivot_counts = pivot_counts.sort_index()

        # Plot the normalized stacked bar chart
        ax = pivot_counts.plot(kind='bar', stacked=True, figsize=(10,6), colormap='Set3')
        
        plt.title(f'Normalized Distribution of UI Value for {ui_key}')
        plt.xlabel('UI Value')
        plt.ylabel('Proportion')
        plt.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('data/plots/ui_plots/' + ui_key + '.pdf')
        plt.close()  # Close the figure to free memory
    except Exception as e:
        print(e)
        pass

# Step 5: Compute raw counts of differences in pairwise region implementations
pairwise_diff_counts = pd.DataFrame(0, index=regions, columns=regions)

for (region1, region2) in combinations(regions, 2):
    diff = (pivot_df[region1] != pivot_df[region2]) & (pivot_df[region1].notnull()) & (pivot_df[region2].notnull())
    count = diff.sum()
    pairwise_diff_counts.loc[region1, region2] = count
    pairwise_diff_counts.loc[region2, region1] = count  # Symmetric matrix

# Step 6: Plot a heatmap of pairwise differences
plt.figure(figsize=(8,6))
sns.heatmap(pairwise_diff_counts, annot=True, fmt='d', cmap='YlGnBu')
plt.title('Pairwise Differences in UI Settings Between Regions')
plt.xlabel('Region')
plt.ylabel('Region')
plt.tight_layout()
plt.savefig('data/plots/ui_pairwise_diff_heatmap.pdf')
plt.close()  # Close the figure to free memory



# Step 4: Plot normalized stacked histograms for each UI setting key
for ui_key in pivot_df['ui_key'].unique():
    try:
        # ... [existing code inside the loop]

        # Save counts DataFrame to CSV
        counts.to_csv('data/plots/ui_plots/' + ui_key + '_counts.csv', index=False)

    except Exception as e:
        print(e)
        pass

# Step 5: Compute raw counts of differences in pairwise region implementations
# ... [existing code for pairwise_diff_counts]

# Step 6: Plot a heatmap of pairwise differences
# ... [existing code for plotting the heatmap]

# Write the pivot_df DataFrame to a CSV file
pivot_df.to_csv('cmp_ui_results.csv', index=False)

# Write the pairwise_diff_counts DataFrame to a CSV file
pairwise_diff_counts.to_csv('data/plots/ui_pairwise_diff_counts.csv')
