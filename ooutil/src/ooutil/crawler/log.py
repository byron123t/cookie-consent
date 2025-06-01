"""Log for file-based scanners."""

from pathlib import Path
import json

# from ooutil.json_util
class JSONable:
    def to_json(self, path: Path=None, verbose=0):
        json_str = json.dumps(self.__dict__, indent=4, sort_keys=True)
        if path is not None:
            path.write_text(json_str)
            if verbose >= 2: print(f'Written to {path}')
        return json_str

class Log(JSONable):
    def __init__(self):
        self.error = None
        self.warnings = []
