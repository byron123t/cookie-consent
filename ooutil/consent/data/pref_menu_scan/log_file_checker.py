"""Check existence of log.json files."""

from pathlib import Path
import json

from consent.consistency.util import get_scan_dirs

def is_json_file_valid(afile: Path):
    try:
        json.loads(afile.read_text())
        return True
    except:
        pass
    return False


SCAN_DIRS = get_scan_dirs('eu')
missing_log_sites = []
corrupt_log_sites = []
for scan_dir in SCAN_DIRS:
    for site_dir in scan_dir.glob('*'):
        site = site_dir.name
        log_file = site_dir / 'log.json'
        if not log_file.exists():
            missing_log_sites.append(site)
        elif not is_json_file_valid(log_file):
            corrupt_log_sites.append(site)

print(f"Missing log files in {len(missing_log_sites):,d} sites:")
print(missing_log_sites)
print(f"Corrupted log files in {len(corrupt_log_sites):,d} sites:")
print(corrupt_log_sites)