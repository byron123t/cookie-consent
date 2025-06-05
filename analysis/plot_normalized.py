import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import scikit_posthocs as sp


# Define regions and conditions
plt.rcParams.update({'font.size': 16})

regions = ['ca', 'eu', 'uk', 'au', 'us', 'sg', 'can', 'za']
conditions = ['comply', 'omit', 'incorrect', 'ambiguous']
condition_convert = {'comply': 'Comply', 'omit': 'Undeclared Cookies', 'incorrect': 'Ignored Rejection', 'ambiguous': 'Wrong Category'}

# Initialize dictionaries to hold total cookie counts and violations for each condition
cookie_counts_per_region = {region: [] for region in regions}
violation_counts_per_region = {region: {condition: [] for condition in conditions} for region in regions}

# Process data for each region and iteration
for region in regions:
    for iteration in range(0, 10):
        file_path = f'data/regions/{region}/scan_0k_20k_comply_{iteration}.parquet'
        try:
            df = pq.read_table(file_path).to_pandas()
            df = df[df['contains_personal_info'] != 'False']
            # Compute total cookie counts
            total_cookies = len(df)
            # Append to the region's list
            cookie_counts_per_region[region].append(total_cookies)
            # Compute violation counts for each condition
            for condition in conditions:
                violation_df = df[df['comply'] == condition]
                total_violation_cookies = len(violation_df)
                violation_counts_per_region[region][condition].append(total_violation_cookies)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# Prepare data for plotting total cookie counts
regions_labels = regions
mean_total_cookies_list = []
std_total_cookies_list = []

for region in regions:
    mean_total_cookies = np.mean(cookie_counts_per_region[region])
    std_total_cookies = np.std(cookie_counts_per_region[region])
    mean_total_cookies_list.append(mean_total_cookies)
    std_total_cookies_list.append(std_total_cookies)

# Plot total cookie counts per region
x_pos = np.arange(len(regions_labels))
colors = plt.cm.Set3(np.linspace(0, 1, len(regions_labels)))

print("Mean Total Cookie Counts per Site:")
print(regions_labels)
print(mean_total_cookies_list)
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x_pos, mean_total_cookies_list, yerr=std_total_cookies_list, align='center', alpha=0.7, capsize=10, color=colors)
ax.set_ylabel('Total Cookie Counts')
ax.set_xticks(x_pos)
ax.set_xticklabels(regions_labels)
ax.set_title('Total Cookie Counts per Region')
ax.yaxis.grid(True)

plt.tight_layout()
plt.savefig('data/plots/total_cookies.pdf')
plt.show()

# Plot normalized violation counts per region for each condition
for condition in conditions:
    mean_normalized_violation_list = []
    std_normalized_violation_list = []
    for region in regions:
        # Get violation counts and total cookie counts per iteration
        violation_counts = violation_counts_per_region[region][condition]
        total_counts = cookie_counts_per_region[region]
        # Calculate normalized violation counts per iteration
        normalized_violation_counts = [v / t if t > 0 else 0 for v, t in zip(violation_counts, total_counts)]
        # Calculate mean and std deviation
        mean_normalized_violation = np.mean(normalized_violation_counts)
        std_normalized_violation = np.std(normalized_violation_counts)
        mean_normalized_violation_list.append(mean_normalized_violation)
        std_normalized_violation_list.append(std_normalized_violation)

    print(condition, 'Normalized Violation Proportion')
    print(regions_labels)
    print(mean_normalized_violation_list)
    # Plotting the normalized violation counts
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x_pos, mean_normalized_violation_list, yerr=std_normalized_violation_list, align='center', alpha=0.7, capsize=10, color=colors)
    ax.set_ylabel(f'Normalized Violation Proportion ({condition_convert[condition]})')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(regions_labels)
    ax.set_title(f'Normalized Violation Proportion per Region - {condition_convert[condition]}')
    ax.yaxis.grid(True)
    # Format y-axis as percentages
    if condition != 'ambiguous':
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
    plt.tight_layout()
    # Save the plot with the specified filename
    plt.savefig(f'data/plots/normalized_violations_{condition}.pdf')
    plt.show()
    
    
with open('data/detector_copy_results.csv', 'w') as f:
    f.write('Region,TotalCookies\n')
    for region in regions:
        for value in cookie_counts_per_region[region]:
            f.write(f'{region},{value}\n')

    for condition in conditions:
        f.write(f'{condition.capitalize()} Normalized Violation Counts (%)\n')
        f.write('Region,NormalizedViolation\n')
        for region in regions:
            for idx in range(len(violation_counts_per_region[region][condition])):
                mean_violation_cookies = violation_counts_per_region[region][condition][idx]
                mean_total_cookies = cookie_counts_per_region[region][idx]
                normalized_violation = (mean_violation_cookies / mean_total_cookies) * 100 if mean_total_cookies != 0 else 0
                f.write(f'{region},{normalized_violation}\n')

    
    
regions = ['ca', 'eu', 'uk', 'au', 'us', 'sg', 'can', 'za']
conditions = ['comply', 'omit', 'incorrect', 'ambiguous']

cookie_counts_per_region = {region: [] for region in regions}
violation_counts_per_region = {region: {condition: [] for condition in conditions} for region in regions}

for region in regions:
    for iteration in range(0, 10):
        file_path = f'data/regions/{region}/scan_0k_20k_comply_{iteration}.parquet'
        try:
            df = pq.read_table(file_path).to_pandas()
            df = df[df['contains_personal_info'] != 'False']
            total_cookies = len(df)
            cookie_counts_per_region[region].append(total_cookies)
            for condition in conditions:
                violation_df = df[df['comply'] == condition]
                total_violation_cookies = len(violation_df)
                violation_counts_per_region[region][condition].append(total_violation_cookies)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

regions_labels = [region.upper() for region in regions]
mean_total_cookies_list = []
std_total_cookies_list = []

for region in regions:
    mean_total_cookies = np.mean(cookie_counts_per_region[region])
    std_total_cookies = np.std(cookie_counts_per_region[region])
    mean_total_cookies_list.append(mean_total_cookies)
    std_total_cookies_list.append(std_total_cookies)

x_pos = np.arange(len(regions_labels))
colors = plt.cm.Set3(np.linspace(0, 1, len(regions_labels)))

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x_pos, mean_total_cookies_list, yerr=std_total_cookies_list, align='center', alpha=0.7, capsize=10, color=colors)
ax.set_ylabel('Total Cookie Counts')
ax.set_xticks(x_pos)
ax.set_xticklabels(regions_labels)
ax.set_title('Total Cookie Counts per Region')
ax.yaxis.grid(True)

plt.tight_layout()
plt.savefig('data/plots/total_cookies.pdf')
plt.show()

for condition in conditions:
    mean_normalized_violation_list = []
    std_normalized_violation_list = []
    for region in regions:
        violation_counts = violation_counts_per_region[region][condition]
        total_counts = cookie_counts_per_region[region]
        normalized_violation_counts = [v / t if t > 0 else 0 for v, t in zip(violation_counts, total_counts)]
        mean_normalized_violation = np.mean(normalized_violation_counts)
        std_normalized_violation = np.std(normalized_violation_counts)
        mean_normalized_violation_list.append(mean_normalized_violation)
        std_normalized_violation_list.append(std_normalized_violation)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x_pos, mean_normalized_violation_list, yerr=std_normalized_violation_list, align='center', alpha=0.7, capsize=10, color=colors)
    ax.set_ylabel(f'Normalized Violation Proportion ({condition.capitalize()})')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(regions_labels)
    ax.set_title(f'Normalized Violation Proportion per Region - {condition.capitalize()}')
    ax.yaxis.grid(True)
    if condition != 'ambiguous':
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
    plt.tight_layout()
    plt.savefig(f'data/plots/normalized_violations_{condition}.pdf')
    plt.show()



total_cookies_data = []
for region in regions:
    for value in cookie_counts_per_region[region]:
        total_cookies_data.append({'Region': region, 'TotalCookies': value})

total_cookies_df = pd.DataFrame(total_cookies_data)

print("Normality Test for Total Cookies per Region:")
normal = True
for region in regions:
    data = total_cookies_df[total_cookies_df['Region'] == region]['TotalCookies']
    stat, p = stats.shapiro(data)
    print(f'Region: {region}, Shapiro-Wilk p-value: {p}')
    if p < 0.05:
        normal = False

data_groups = [total_cookies_df[total_cookies_df['Region'] == region]['TotalCookies'] for region in regions]
stat, p = stats.levene(*data_groups)
print(f'\nLevene’s Test p-value for Total Cookies per Region: {p}')

if normal and p >= 0.05:
    # ANOVA
    f_stat, p_val = stats.f_oneway(*data_groups)
    print(f'\nANOVA F-statistic: {f_stat}, p-value: {p_val}')
else:
    # Kruskal-Wallis Test
    h_stat, p_val = stats.kruskal(*data_groups)
    print(f'\nKruskal-Wallis H-statistic: {h_stat}, p-value: {p_val}')

# Post-hoc analysis if significant
if p_val < 0.05:
    posthoc = sp.posthoc_dunn(total_cookies_df, val_col='TotalCookies', group_col='Region', p_adjust='bonferroni')
    print('\nPost-hoc Dunn’s test results for Total Cookies per Region:')
    print(posthoc)

# Statistical analysis for normalized violation counts per condition
for condition in conditions:
    violation_data = []
    for region in regions:
        for idx in range(len(violation_counts_per_region[region][condition])):
            violation_count = violation_counts_per_region[region][condition][idx]
            total_count = cookie_counts_per_region[region][idx]
            normalized_violation = (violation_count / total_count) * 100 if total_count != 0 else 0
            violation_data.append({'Region': region, 'NormalizedViolation': normalized_violation})

    violation_df = pd.DataFrame(violation_data)

    # Shapiro-Wilk Test for normality
    print(f"\nNormality Test for Normalized Violation Counts ({condition.capitalize()}):")
    normal = True
    for region in regions:
        data = violation_df[violation_df['Region'] == region]['NormalizedViolation']
        stat, p = stats.shapiro(data)
        print(f'Region: {region}, Shapiro-Wilk p-value: {p}')
        if p < 0.05:
            normal = False

    # Levene's Test for homogeneity of variances
    data_groups = [violation_df[violation_df['Region'] == region]['NormalizedViolation'] for region in regions]
    stat, p = stats.levene(*data_groups)
    print(f'\nLevene’s Test p-value for Normalized Violation Counts ({condition.capitalize()}): {p}')

    # Decide which test to use
    if normal and p >= 0.05:
        # ANOVA
        f_stat, p_val = stats.f_oneway(*data_groups)
        print(f'\nANOVA F-statistic for {condition.capitalize()}: {f_stat}, p-value: {p_val}')
    else:
        # Kruskal-Wallis Test
        h_stat, p_val = stats.kruskal(*data_groups)
        print(f'\nKruskal-Wallis H-statistic for {condition.capitalize()}: {h_stat}, p-value: {p_val}')

    # Post-hoc analysis if significant
    if p_val < 0.05:
        posthoc = sp.posthoc_dunn(violation_df, val_col='NormalizedViolation', group_col='Region', p_adjust='bonferroni')
        print(f'\nPost-hoc Dunn’s test results for Normalized Violation Counts ({condition.capitalize()}):')
        print(posthoc)
