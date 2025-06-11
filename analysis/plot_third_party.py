import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import scikit_posthocs as sp

# Define regions and conditions
plt.rcParams.update({'pdf.fonttype': 42})
plt.rcParams.update({'ps.fonttype': 42})
plt.rcParams.update({'font.size': 16})

regions = ['ca', 'eu', 'uk', 'au', 'us', 'sg', 'can', 'za']
conditions = ['comply', 'omit', 'incorrect', 'ambiguous']
condition_convert = {'comply': 'Comply', 'omit': 'Undeclared Cookies', 'incorrect': 'Ignored Rejection', 'ambiguous': 'Wrong Category'}

# Initialize dictionaries to hold cookie counts and violations for each condition
cookie_counts_per_region = {region: [] for region in regions}
violation_counts_per_region = {region: {condition: [] for condition in conditions} for region in regions}

# Process data for each region and iteration
for region in regions:
    for iteration in range(0, 10):
        file_path = f'data/regions/{region}/scan_0k_20k_comply_{iteration}.parquet'
        # try:
        df = pq.read_table(file_path).to_pandas()
        df = df[df['contains_personal_info'] != 'False']
        # Only consider third-party cookies where 'domain' != 'site'
        vectorized_contains = np.vectorize(lambda site, domain: site in domain)
        mask = vectorized_contains(df['site'], df['domain'])
        df = df[~mask]
        # Compute total cookie counts per site
        total_cookies_per_site = df.groupby('site').size()
        # Compute mean total cookies per site
        mean_total_cookies = total_cookies_per_site.mean()
        # Append to the region's list
        cookie_counts_per_region[region].append(mean_total_cookies)
        # Compute violation counts per site for each condition
        for condition in conditions:
            violation_df = df[df['comply'] == condition]
            violation_cookies_per_site = violation_df.groupby('site').size()
            mean_violation_cookies = violation_cookies_per_site.mean()
            violation_counts_per_region[region][condition].append(mean_violation_cookies)
            # if condition == 'omit':
            #     print(region.upper())
            #     print('---')
            #     print(violation_df['site'])
            #     print(violation_df['domain'])
            #     print(violation_df['name'])
        continue
        # except Exception as e:
        #     print(f"Error processing {file_path}: {e}")

# Prepare data for plotting total cookie counts
regions_labels = [region.upper() for region in regions]
mean_total_cookies_list = []
std_total_cookies_list = []

for region in regions:
    mean_total_cookies = np.mean(cookie_counts_per_region[region])
    std_total_cookies = np.std(cookie_counts_per_region[region])
    mean_total_cookies_list.append(mean_total_cookies)
    std_total_cookies_list.append(std_total_cookies)

# Print mean total cookie counts per site per region
print("Mean Total Cookie Counts per Site:")
print(regions_labels)
print(mean_total_cookies_list)

# Plot mean total cookie counts per site per region
x_pos = np.arange(len(regions_labels))
colors = plt.cm.Set3(np.linspace(0, 1, len(regions_labels)))

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x_pos, mean_total_cookies_list, yerr=std_total_cookies_list, align='center', alpha=0.7, capsize=10, color=colors)
ax.set_ylabel('Mean Total Cookie Counts per Site')
ax.set_xticks(x_pos)
ax.set_xticklabels(regions_labels)
ax.set_title('Mean Total Cookie Counts per Site per Region')
ax.yaxis.grid(True)

plt.tight_layout()
plt.savefig(f'data/plots/3rd_party_mean_total_cookies.pdf')
plt.show()


# Statistical analysis for mean total cookie counts per site
total_cookies_data = []
for region in regions:
    for value in cookie_counts_per_region[region]:
        total_cookies_data.append({'Region': region, 'MeanTotalCookies': value})

total_cookies_df = pd.DataFrame(total_cookies_data)

# Shapiro-Wilk Test for normality
print("Normality Test for Mean Total Cookies per Site:")
normal = True
for region in regions:
    data = total_cookies_df[total_cookies_df['Region'] == region]['MeanTotalCookies']
    if len(data) >= 3:  # Shapiro-Wilk test requires at least 3 data points
        stat, p = stats.shapiro(data)
        print(f'Region: {region}, Shapiro-Wilk p-value: {p}')
        if p < 0.05:
            normal = False
    else:
        print(f'Region: {region}, Not enough data for Shapiro-Wilk test.')
        normal = False

# Levene's Test for homogeneity of variances
data_per_region = [total_cookies_df[total_cookies_df['Region'] == region]['MeanTotalCookies'] for region in regions]
stat, p = stats.levene(*data_per_region)
print(f'\nLevene’s Test p-value for Mean Total Cookies per Site: {p}')

# Decide which test to use
if normal and p >= 0.05:
    # ANOVA
    f_stat, p_val = stats.f_oneway(*data_per_region)
    print(f'\nANOVA F-statistic: {f_stat}, p-value: {p_val}')
else:
    # Kruskal-Wallis Test
    h_stat, p_val = stats.kruskal(*data_per_region)
    print(f'\nKruskal-Wallis H-statistic: {h_stat}, p-value: {p_val}')

# Post-hoc analysis if significant
if p_val < 0.05:
    posthoc = sp.posthoc_dunn(total_cookies_df, val_col='MeanTotalCookies', group_col='Region', p_adjust='bonferroni')
    print('\nPost-hoc Dunn’s test results for Mean Total Cookies per Site:')
    print(posthoc)

# Prepare data for plotting normalized violation counts as percentages
for condition in conditions:
    normalized_violation_list = []
    std_normalized_violation_list = []
    for idx, region in enumerate(regions):
        mean_violation_cookies = np.mean(violation_counts_per_region[region][condition])
        std_violation_cookies = np.std(violation_counts_per_region[region][condition])
        mean_total_cookies = mean_total_cookies_list[idx]  # Corresponding total mean cookies for the region
        std_total_cookies = std_total_cookies_list[idx]
        # Compute normalized violation (mean violation cookies per site / mean total cookies per site) as percentage
        if mean_total_cookies != 0:
            normalized_violation = (mean_violation_cookies / mean_total_cookies) * 100
            # For standard deviation, use error propagation formula for division and multiply by 100
            std_normalized_violation = normalized_violation * np.sqrt(
                (std_violation_cookies / mean_violation_cookies)**2 +
                (std_total_cookies / mean_total_cookies)**2
            ) if mean_violation_cookies != 0 else 0
        else:
            normalized_violation = 0
            std_normalized_violation = 0
        normalized_violation_list.append(normalized_violation)
        std_normalized_violation_list.append(std_normalized_violation)
    
    # Print normalized violation counts per site per region
    print(f"{condition.capitalize()} Normalized Violation Counts (%):")
    print(regions_labels)
    print(normalized_violation_list)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x_pos, normalized_violation_list, yerr=std_normalized_violation_list, align='center', alpha=0.7, capsize=10, color=colors)
    ax.set_ylabel(f'Normalized Violation Counts (%) ({condition_convert[condition]})')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(regions_labels)
    ax.set_title(f'Normalized Violation Counts per Site per Region - {condition_convert[condition]}')
    ax.yaxis.grid(True)
    
    # Adjust y-axis to show percentage signs
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}%'.format(y)))
    
    plt.tight_layout()
    plt.savefig(f'data/plots/3rd_party_mean_normalized_violations_{condition}.pdf')
    plt.show()
    
    # Statistical analysis for normalized violation counts per condition
    violation_data = []
    for region in regions:
        for idx in range(len(violation_counts_per_region[region][condition])):
            mean_violation_cookies = violation_counts_per_region[region][condition][idx]
            mean_total_cookies = cookie_counts_per_region[region][idx]
            normalized_violation = (mean_violation_cookies / mean_total_cookies) * 100 if mean_total_cookies != 0 else 0
            violation_data.append({'Region': region, 'NormalizedViolation': normalized_violation})

    violation_df = pd.DataFrame(violation_data)

    # Shapiro-Wilk Test for normality
    print(f"\nNormality Test for Normalized Violation Counts ({condition.capitalize()}):")
    normal = True
    for region in regions:
        data = violation_df[violation_df['Region'] == region]['NormalizedViolation']
        if len(data) >= 3:
            stat, p = stats.shapiro(data)
            print(f'Region: {region}, Shapiro-Wilk p-value: {p}')
            if p < 0.05:
                normal = False
        else:
            print(f'Region: {region}, Not enough data for Shapiro-Wilk test.')
            normal = False

    # Levene's Test for homogeneity of variances
    data_per_region = [violation_df[violation_df['Region'] == region]['NormalizedViolation'] for region in regions]
    stat, p = stats.levene(*data_per_region)
    print(f'\nLevene’s Test p-value for Normalized Violation Counts ({condition.capitalize()}): {p}')

    # Decide which test to use
    if normal and p >= 0.05:
        # ANOVA
        f_stat, p_val = stats.f_oneway(*data_per_region)
        print(f'\nANOVA F-statistic for {condition.capitalize()}: {f_stat}, p-value: {p_val}')
    else:
        # Kruskal-Wallis Test
        h_stat, p_val = stats.kruskal(*data_per_region)
        print(f'\nKruskal-Wallis H-statistic for {condition.capitalize()}: {h_stat}, p-value: {p_val}')

    # Post-hoc analysis if significant
    if p_val < 0.05:
        posthoc = sp.posthoc_dunn(violation_df, val_col='NormalizedViolation', group_col='Region', p_adjust='bonferroni')
        print(f'\nPost-hoc Dunn’s test results for Normalized Violation Counts ({condition.capitalize()}):')
        print(posthoc)
        
with open('data/3rd_party_results.csv', 'w') as f:
    f.write('Region,MeanTotalCookies\n')
    for region, mean_total_cookies in zip(regions, mean_total_cookies_list):
        f.write(f'{region},{mean_total_cookies}\n')
    f.write('\n')
    for region in regions:
        for condition in conditions:
            f.write(f'Region,{condition.capitalize()}NormalizedViolation\n')
            for value in violation_counts_per_region[region][condition]:
                mean_total_cookies = np.mean(cookie_counts_per_region[region])
                normalized_violation = (value / mean_total_cookies) * 100 if mean_total_cookies != 0 else 0
                f.write(f'{region},{normalized_violation}\n')
