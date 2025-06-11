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
regions = ['CA', 'EU', 'UK', 'AU', 'US', 'SG', 'CAN', 'ZA']
conditions = ['comply', 'omit', 'incorrect', 'ambiguous']
condition_convert = {'comply': 'Comply', 'omit': 'Undeclared Cookies', 'incorrect': 'Ignored Rejection', 'ambiguous': 'Wrong Category'}
iterations = range(0, 10)

site_counts_per_region = {region: {} for region in regions}

# Data Aggregation
for region in regions:
    site_counts = {}
    for iteration in iterations:
        file_path = f'data/regions/{region.lower()}/scan_0k_20k_comply_{iteration}.parquet'
        try:
            df = pq.read_table(file_path).to_pandas()
            df = df[df['contains_personal_info'] != 'False']
            for site, group in df.groupby('site'):
                total_cookies = len(group)
                violation_counts = group['comply'].value_counts().to_dict()
                if site not in site_counts:
                    site_counts[site] = {'total_cookies': [], 'violation_counts': {cond: [] for cond in conditions}}
                site_counts[site]['total_cookies'].append(total_cookies)
                for condition in conditions:
                    count = violation_counts.get(condition, 0)
                    site_counts[site]['violation_counts'][condition].append(count)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    site_counts_per_region[region] = site_counts

# Prepare DataFrames
total_cookies_df = pd.DataFrame()
violation_counts_df = {condition: pd.DataFrame() for condition in conditions}
normalized_violation_df = {condition: pd.DataFrame() for condition in conditions}

for region in regions:
    site_counts = site_counts_per_region[region]
    for site in site_counts:
        mean_total_cookies = np.mean(site_counts[site]['total_cookies'])
        total_cookies_df.loc[site, region] = mean_total_cookies
        for condition in conditions:
            mean_violation = np.mean(site_counts[site]['violation_counts'][condition])
            violation_counts_df[condition].loc[site, region] = mean_violation
            # Calculate normalized violation percentage
            if mean_total_cookies != 0:
                mean_normalized_violation = (mean_violation / mean_total_cookies) * 100
            else:
                mean_normalized_violation = np.nan
            normalized_violation_df[condition].loc[site, region] = mean_normalized_violation

# Plotting Mean Differences Compared to EU
regions_except_eu = [region for region in regions if region != 'EU']

total_cookies_diff_df = total_cookies_df[regions_except_eu].subtract(total_cookies_df['EU'], axis=0)
mean_total_cookies_diff = total_cookies_diff_df.mean()

fig, ax = plt.subplots(figsize=(10, 6))

# **Uppercase the index to change x-axis labels**
mean_total_cookies_diff.index = mean_total_cookies_diff.index.str.upper()  # <-- Added this line

mean_total_cookies_diff.plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')
ax.set_ylabel('Mean Difference in Total Cookies per Site')
ax.set_title('Mean Difference in Total Cookies per Site Compared to EU')
ax.axhline(0, color='black', linewidth=0.8)
plt.tight_layout()
plt.savefig('data/plots/mean_difference_total_cookies.pdf')
plt.show()

for condition in conditions:
    violation_diff_df = violation_counts_df[condition][regions_except_eu].subtract(violation_counts_df[condition]['EU'], axis=0)
    mean_violation_diff = violation_diff_df.mean()

    # **Uppercase the index to change x-axis labels**
    mean_violation_diff.index = mean_violation_diff.index.str.upper()  # <-- Added this line

    fig, ax = plt.subplots(figsize=(10, 6))
    mean_violation_diff.plot(kind='bar', ax=ax, color='skyblue', edgecolor='black')
    ax.set_ylabel(f'Mean Difference in {condition_convert[condition]} Violations per Site')
    ax.set_title(f'Mean Difference in {condition_convert[condition]} Violations per Site Compared to EU')
    ax.axhline(0, color='black', linewidth=0.8)
    plt.tight_layout()
    plt.savefig(f'data/plots/mean_difference_violations_{condition}.pdf')
    plt.show()
    
# Assuming 'conditions' and 'condition_convert' are defined
conditions = ['omit', 'incorrect', 'ambiguous']
condition_convert = {'comply': 'Comply', 'omit': 'Undeclared Cookies', 'incorrect': 'Ignored Rejection', 'ambiguous': 'Wrong Category'}

# Combine mean differences for all conditions into one DataFrame
mean_violation_diff_combined = pd.DataFrame()

for condition in conditions:
    violation_diff_df = violation_counts_df[condition][regions_except_eu].subtract(violation_counts_df[condition]['EU'], axis=0)
    mean_violation_diff = violation_diff_df.mean()
    mean_violation_diff_combined[condition_convert[condition]] = mean_violation_diff

# Uppercase the index to change x-axis labels
mean_violation_diff_combined.index = mean_violation_diff_combined.index.str.upper()

# Plot the combined mean differences
fig, ax = plt.subplots(figsize=(10, 6))
mean_violation_diff_combined.plot(kind='bar', ax=ax, edgecolor='black')
ax.set_ylabel('Mean Difference in Violations per Site')
ax.set_title('Mean Difference in Violations per Site Compared to EU')
ax.axhline(0, color='black', linewidth=0.8)
plt.tight_layout()
plt.savefig('data/plots/mean_difference_violations_combined.pdf')
plt.show()
    

with open('data/website_analysis_results.csv', 'w') as f:
    f.write('Site,Region,MeanTotalCookies\n')
    for site in total_cookies_df.index:
        for region in regions:
            value = total_cookies_df.loc[site, region]
            f.write(f'{site},{region},{value}\n')

    for condition in conditions:
        f.write(f'{condition.capitalize()}NormalizedViolation\n')
        for site in normalized_violation_df[condition].index:
            for region in regions:
                value = normalized_violation_df[condition].loc[site, region]
                f.write(f'{site},{region},{value}\n')


    
    
import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import scikit_posthocs as sp

# Define regions and conditions
plt.rcParams.update({'font.size': 16})
regions = ['CA', 'EU', 'UK', 'AU', 'US', 'SG', 'CAN', 'ZA']
conditions = ['incorrect', 'omit', 'ambiguous']
iterations = range(0, 10)

# Initialize dictionaries to hold cookie counts and violations for each condition
cookie_counts_per_region = {region: [] for region in regions}
violation_counts_per_region = {region: {condition: [] for condition in conditions} for region in regions}

# Data Aggregation
for region in regions:
    for iteration in iterations:
        file_path = f'data/regions/{region.lower()}/scan_0k_20k_comply_{iteration}.parquet'
        try:
            df = pq.read_table(file_path).to_pandas()
            df = df[df['contains_personal_info'] != 'False']
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
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# Prepare data for plotting normalized violation counts as percentages
regions_labels = [region.upper() for region in regions]
x_pos = np.arange(len(regions_labels))
colors = ['red', 'blue', 'green']  # Colors for each condition

print(regions_labels)

# Initialize data structures for plotting
normalized_violation_data = []
std_normalized_violation_data = []

for condition in conditions:
    normalized_violation_list = []
    std_normalized_violation_list = []
    for idx, region in enumerate(regions):
        # Lists to hold normalized violations for each iteration
        normalized_violations_iterations = []
        for i in range(len(cookie_counts_per_region[region])):
            mean_violation_cookies = violation_counts_per_region[region][condition][i]
            mean_total_cookies = cookie_counts_per_region[region][i]
            if mean_total_cookies != 0:
                normalized_violation = (mean_violation_cookies / mean_total_cookies) * 100
                normalized_violations_iterations.append(normalized_violation)
        # Calculate mean and standard deviation of normalized violations for this region and condition
        mean_normalized_violation = np.mean(normalized_violations_iterations)
        std_normalized_violation = np.std(normalized_violations_iterations)
        normalized_violation_list.append(mean_normalized_violation)
        std_normalized_violation_list.append(std_normalized_violation)
    normalized_violation_data.append(normalized_violation_list)
    std_normalized_violation_data.append(std_normalized_violation_list)

# Plotting the combined grouped bar chart
bar_width = 0.25  # Width of each bar
fig, ax = plt.subplots(figsize=(12, 8))

for idx, condition in enumerate(conditions):
    # Calculate position for each condition
    positions = x_pos + (idx - 1) * bar_width
    ax.bar(positions, normalized_violation_data[idx], yerr=std_normalized_violation_data[idx],
           width=bar_width, align='center', alpha=0.7, capsize=5,
           label=condition_convert[condition], color=colors[idx])

ax.set_ylabel('Normalized Violation Counts (%)')
ax.set_xticks(x_pos)
regions_labels = [region.upper() for region in regions]
ax.set_xticklabels(regions_labels)
print(regions_labels)
ax.set_title('Normalized Violation Counts per Site per Region')
ax.yaxis.grid(True)
ax.legend()

# Adjust y-axis to show percentage signs
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}%'.format(y)))

# Adjust x-axis limits to fit all bars
ax.set_xlim([x_pos[0] - bar_width, x_pos[-1] + bar_width])

plt.tight_layout()
plt.savefig('data/plots/mean_normalized_violations_combined.pdf')
plt.show()
    
    

# Statistical Analysis for Mean Total Cookies per Site

# Reshape Data for Statistical Tests
total_cookies_melted = total_cookies_df.reset_index().melt(id_vars='index', var_name='Region', value_name='MeanTotalCookies').rename(columns={'index': 'Site'})
total_cookies_melted = total_cookies_melted.dropna()

# Shapiro-Wilk Test for Normality
print("Normality Test for Mean Total Cookies per Site:")
normal = True
for region in regions:
    data = total_cookies_melted[total_cookies_melted['Region'] == region]['MeanTotalCookies']
    if len(data) < 3:
        print(f'Region: {region}, not enough data for Shapiro-Wilk test')
        normal = False
        continue
    stat, p = stats.shapiro(data)
    print(f'Region: {region}, Shapiro-Wilk p-value: {p}')
    if p < 0.05:
        normal = False

# Levene's Test for Homogeneity of Variances
data_per_region = [total_cookies_melted[total_cookies_melted['Region'] == region]['MeanTotalCookies'] for region in regions]
stat, p = stats.levene(*data_per_region)
print(f'\nLevene’s Test p-value for Mean Total Cookies per Site: {p}')
equal_variances = p >= 0.05

# Decide on Statistical Test
if normal and equal_variances:
    # ANOVA
    f_stat, p_val = stats.f_oneway(*data_per_region)
    print(f'\nANOVA F-statistic: {f_stat}, p-value: {p_val}')
else:
    # Kruskal-Wallis Test
    h_stat, p_val = stats.kruskal(*data_per_region)
    print(f'\nKruskal-Wallis H-statistic: {h_stat}, p-value: {p_val}')

# Post-hoc Analysis if Significant
if p_val < 0.05:
    posthoc = sp.posthoc_dunn(total_cookies_melted, val_col='MeanTotalCookies', group_col='Region', p_adjust='bonferroni')
    print('\nPost-hoc Dunn’s test results for Mean Total Cookies per Site:')
    print(posthoc)

# Statistical Analysis for Normalized Violation Counts per Condition

for condition in conditions:
    print(f"\nStatistical Analysis for Normalized {condition.capitalize()} Violations:")
    df = normalized_violation_df[condition].reset_index().melt(id_vars='index', var_name='Region', value_name='NormalizedViolation').rename(columns={'index': 'Site'})
    df = df.dropna()

    # Shapiro-Wilk Test for Normality
    print("Normality Test:")
    normal = True
    for region in regions:
        data = df[df['Region'] == region]['NormalizedViolation']
        if len(data) < 3:
            print(f'Region: {region}, not enough data for Shapiro-Wilk test')
            normal = False
            continue
        stat, p = stats.shapiro(data)
        print(f'Region: {region}, Shapiro-Wilk p-value: {p}')
        if p < 0.05:
            normal = False

    # Levene's Test for Homogeneity of Variances
    data_per_region = [df[df['Region'] == region]['NormalizedViolation'] for region in regions if not df[df['Region'] == region]['NormalizedViolation'].isnull().all()]
    stat, p = stats.levene(*data_per_region)
    print(f'\nLevene’s Test p-value: {p}')
    equal_variances = p >= 0.05

    # Decide on Statistical Test
    if normal and equal_variances:
        # ANOVA
        f_stat, p_val = stats.f_oneway(*data_per_region)
        print(f'\nANOVA F-statistic: {f_stat}, p-value: {p_val}')
    else:
        # Kruskal-Wallis Test
        h_stat, p_val = stats.kruskal(*data_per_region)
        print(f'\nKruskal-Wallis H-statistic: {h_stat}, p-value: {p_val}')

    # Post-hoc Analysis if Significant
    if p_val < 0.05:
        posthoc = sp.posthoc_dunn(df, val_col='NormalizedViolation', group_col='Region', p_adjust='bonferroni')
        print('\nPost-hoc Dunn’s test results:')
        print(posthoc)
