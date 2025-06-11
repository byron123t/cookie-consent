import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import numpy as np

# Define regions and conditions
plt.rcParams.update({'pdf.fonttype': 42})
plt.rcParams.update({'ps.fonttype': 42})
plt.rcParams.update({'font.size': 16})

regions = ['ca', 'eu', 'uk', 'au', 'us', 'sg', 'can', 'za']
conditions = ['omit', 'incorrect', 'ambiguous']
condition_convert = {
    'comply': 'Comply',
    'omit': 'Undeclared Cookies',
    'incorrect': 'Ignored Rejection',
    'ambiguous': 'Wrong Category'
}

# Initialize dictionaries to hold percentages
violation_percentages = {}  # Overall percentage of sites with any violation
violation_percentages_per_condition = {region.upper(): {} for region in regions}  # Per-condition percentages

# Process data for each region and iteration
for region in regions:
    sites_with_violation = set()
    total_sites = set()
    # Initialize a dictionary to hold sites with violations per condition
    sites_with_violation_per_condition = {condition: set() for condition in conditions}
    for iteration in range(0, 10):
        file_path = f'data/regions/{region}/scan_0k_20k_comply_{iteration}.parquet'
        try:
            df = pq.read_table(file_path).to_pandas()
            df = df[df['contains_personal_info'] != 'False']
            # Add all sites to total_sites
            total_sites.update(df['site'].unique())
            # Filter rows where 'comply' is one of the violation conditions
            violation_df = df[df['comply'].isin(conditions)]
            # Add sites with any violation
            sites_with_violation.update(violation_df['site'].unique())
            # For each condition, find sites with that specific violation
            for condition in conditions:
                condition_df = df[df['comply'] == condition]
                sites_with_violation_per_condition[condition].update(condition_df['site'].unique())
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    # Calculate overall percentage of sites with any violation
    if total_sites:
        percentage = (len(sites_with_violation) / len(total_sites)) * 100
        violation_percentages[region.upper()] = percentage
    else:
        violation_percentages[region.upper()] = np.nan
    # Calculate percentage per condition
    for condition in conditions:
        sites_with_violation_condition = sites_with_violation_per_condition[condition]
        if total_sites:
            percentage_condition = (len(sites_with_violation_condition) / len(total_sites)) * 100
            violation_percentages_per_condition[region.upper()][condition] = percentage_condition
        else:
            violation_percentages_per_condition[region.upper()][condition] = np.nan

# Print out the percentages
print("Percentage of Sites with At Least One Violation per Region:")
for region, percentage in violation_percentages.items():
    print(f"{region}: {percentage:.2f}%")

print("\nPercentage of Sites with At Least One Violation per Condition per Region:")
for region in regions:
    region_upper = region.upper()
    print(f"\nRegion: {region_upper}")
    for condition in conditions:
        percentage_condition = violation_percentages_per_condition[region_upper][condition]
        condition_name = condition_convert.get(condition, condition)
        print(f"{condition_name}: {percentage_condition:.2f}%")

# Optional: Plot the percentages

# Optional: Plot the percentages
fig, ax = plt.subplots(figsize=(10, 6))
regions_sorted = sorted(violation_percentages.keys())
percentages = [violation_percentages[region] for region in regions_sorted]
ax.bar(regions_sorted, percentages, color='skyblue', edgecolor='black')
ax.set_ylabel('Percentage of Sites with Violations (%)')
ax.set_title('Percentage of Sites with At Least One Violation per Region')
ax.set_ylim(0, 100)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('data/plots/violation_percentages_per_region.pdf')
plt.show()



import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import numpy as np

# Define regions and conditions
plt.rcParams.update({'font.size': 16})

regions = ['ca', 'eu', 'uk', 'au', 'us', 'sg', 'can', 'za']
conditions = ['omit', 'incorrect', 'ambiguous']
condition_convert = {
    'comply': 'Comply',
    'omit': 'Undeclared Cookies',
    'incorrect': 'Ignored Rejection',
    'ambiguous': 'Wrong Category'
}

# Initialize a dictionary to hold violation counts per region per condition
violation_cookie_counts = {region.upper(): {condition: [] for condition in conditions} for region in regions}

# Process data for each region and iteration
for region in regions:
    for iteration in range(0, 10):
        file_path = f'data/regions/{region}/scan_0k_20k_comply_{iteration}.parquet'
        try:
            df = pq.read_table(file_path).to_pandas()
            df = df[df['contains_personal_info'] != 'False']
            # For each violation condition, filter and count the cookies
            for condition in conditions:
                violation_df = df[df['comply'] == condition]
                count = len(violation_df)
                violation_cookie_counts[region.upper()][condition].append(count)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

# Calculate the average counts per condition per region
average_violation_counts = {region: {} for region in violation_cookie_counts}
for region in violation_cookie_counts:
    for condition in conditions:
        counts = violation_cookie_counts[region][condition]
        if counts:
            average_count = np.sum(counts)
        else:
            average_count = 0
        average_violation_counts[region][condition] = average_count / len(counts) if counts else 0

# Print out the average counts
print("Average Violation Cookie Counts per Region (per iteration):")
for region in average_violation_counts:
    print(f"\nRegion: {region}")
    for condition in conditions:
        condition_name = condition_convert.get(condition, condition)
        count = average_violation_counts[region][condition]
        print(f"{condition_name}: {count:.2f}")

# Plot the average counts per region per condition
fig, ax = plt.subplots(figsize=(12, 8))
regions_sorted = sorted(average_violation_counts.keys())
conditions_sorted = [condition_convert[cond] for cond in conditions]

# Prepare data for plotting
data = {cond: [average_violation_counts[region][cond_key] for region in regions_sorted] 
        for cond_key, cond in zip(conditions, conditions_sorted)}

# Plot grouped bar chart
bar_width = 0.2
index = np.arange(len(regions_sorted))

for i, (cond, counts) in enumerate(data.items()):
    ax.bar(index + i * bar_width, counts, bar_width, label=cond)

ax.set_ylabel('Average Number of Violation Cookies per Iteration')
ax.set_title('Average Violation Cookie Counts per Region (per iteration)')
ax.set_xticks(index + bar_width)
ax.set_xticklabels(regions_sorted, rotation=45)
ax.legend(title='Violation Type')
plt.tight_layout()
plt.savefig('data/plots/average_violation_cookie_counts_per_region.pdf')
plt.show()
