""" Default paths that can be used to access. """
# TODO: move this to ooutil to avoid duplicate with optout.

import uuid

from pathlib import Path
from ooutil import data_path


def get_env_data_dir():
    return data_path.get_env_data_dir(project_name='consent')

def get_env_data_dir2():
    return data_path.get_env_data_dir2(project_name='consent')

# TODO: refactor the following to avoid duplicate code
def get_rel_path(exper_date, sub_dir) -> str:
    return f'{exper_date}/{sub_dir}'


def get_data_dir(rel_path) -> Path:
    """Get a data_dir in the DATA_DIR with rel_path."""
    data_dir = get_env_data_dir() / rel_path
    assert data_dir.exists(), f'{data_dir} not exist.'
    return data_dir


def get_data_sub_dir(exper_date, sub_dir) -> Path:
    """Create a data_dir in the DATA_DIR with rel_path."""
    return get_data_dir(get_rel_path(exper_date, sub_dir))


def create_data_dir(rel_path) -> Path:
    """Create a data_dir in the DATA_DIR with rel_path."""
    data_dir = get_env_data_dir() / rel_path
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def create_data_sub_dir(exper_date, sub_dir) -> Path:
    """Create a data_dir in the DATA_DIR with rel_path."""
    return create_data_dir(get_rel_path(exper_date, sub_dir))

def get_data_dir2(rel_path: str) -> Path:
    """Get a data_dir in the DATA_DIR with rel_path."""
    data_dir = get_env_data_dir2() / rel_path
    assert data_dir.exists(), f'{data_dir} not exist.'
    return data_dir

def create_data_dir2(rel_path: str, exist_ok) -> Path:
    """Create a data_dir in the DATA_DIR with rel_path."""
    data_dir = get_env_data_dir2() / rel_path
    # More error message.
    if not exist_ok and data_dir.exists():
        new_dir = data_dir.parent / f"{data_dir.name}_{str(uuid.uuid4())}"
        print(f"{data_dir} should not exist, rename to {new_dir}")
        data_dir.rename(new_dir)
    data_dir.mkdir(parents=True, exist_ok=exist_ok)
    return data_dir