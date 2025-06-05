"""Path utils."""

from pathlib import Path

import src.ooutil.default_path


PROJECT_NAME = 'consent'

def get_data_dir(rel_path) -> Path:
    return src.ooutil.default_path.get_data_dir(PROJECT_NAME, rel_path)

def create_data_dir(rel_path) -> Path:
    return src.ooutil.default_path.create_data_dir(PROJECT_NAME, rel_path)

def get_autoconsent_dir():
    raise NotImplementedError
    # TODO: change to use Path(__file__)
    adir = ooutil.default_path.get_project_dir() / 'src/consent/bannerscan/autoconsent'
    assert adir.exists()
    return adir

def get_tmp_dir():
    tmp_dir = Path.home() / 'tmp'
    assert tmp_dir.exists() and tmp_dir.is_dir(), f'{tmp_dir=} invalid'
    return tmp_dir

if __name__ == '__main__':
    print(get_autoconsent_dir())
