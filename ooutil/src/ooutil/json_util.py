"""Json file utils."""

from json.decoder import JSONDecodeError
from pathlib import Path
import json
import traceback

import pandas as pd


def read_json_file(file_path: Path, raise_exception=True):
    try:
        return json.loads(file_path.read_text())
    except (JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}, {type(e).__name__} {e}") # , {traceback.format_exc()}")
        if raise_exception:
            raise e
    return None


def dump_to_json_file(obj, out_file: Path):
    out_file.write_text(json.dumps(obj, indent=4, sort_keys=True))


def dump_json_obj_dict(obj, out_file: Path=None):
    """Get json of an object's __dict__"""
    json_str = json.dumps(obj, indent=4, sort_keys=True, default=lambda o: o.__dict__)
    if out_file is not None:
        out_file.write_text(json_str)
    return json_str


def read_json_file_to_df(file_path: Path):
    return pd.DataFrame(read_json_file(file_path))

