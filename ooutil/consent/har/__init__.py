from pathlib import Path

def get_har_dump_script_path() -> Path:
    return Path(__file__).parent / 'har_dump.py'
