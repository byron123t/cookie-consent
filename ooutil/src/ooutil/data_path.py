""" Default paths that can be used to access. """

import os

from pathlib import Path
# from dotenv import load_dotenv, find_dotenv

def is_in_docker() -> bool:
    return os.environ.get('AM_I_IN_A_DOCKER_CONTAINER') is not None

def get_env_data_dir(project_name) -> Path:
    # dotenv_file = find_dotenv()
    # assert dotenv_file != '', 'Cannot find .env file'
    # print(dotenv_file)
    # load_dotenv(verbose=True)
    
    DATA_DIR = Path("./data")
    return DATA_DIR

def get_env_data_dir2(project_name) -> Path:
    # dotenv_file = find_dotenv()
    # assert dotenv_file != '', 'Cannot find .env file'
    # print(dotenv_file)
    # load_dotenv(verbose=True)
    DATA_DIR = Path("./data")
    return DATA_DIR


# TODO: refactor the following to avoid duplicate code
# def get_rel_path(exper_date, sub_dir):
#     return f'{exper_date}/{sub_dir}'


# def get_data_dir(rel_path):
#     """Get a data_dir in the DATA_DIR with rel_path."""
#     data_dir = get_env_data_dir() / rel_path
#     assert data_dir.exists(), f'{data_dir} not exist.'
#     return data_dir


# def get_data_sub_dir(exper_date, sub_dir):
#     """Create a data_dir in the DATA_DIR with rel_path."""
#     return get_data_dir(get_rel_path(exper_date, sub_dir))


# def create_data_dir(rel_path):
#     """Create a data_dir in the DATA_DIR with rel_path."""
#     data_dir = get_env_data_dir() / rel_path
#     data_dir.mkdir(parents=True, exist_ok=True)
#     return data_dir


# def create_data_sub_dir(exper_date, sub_dir):
#     """Create a data_dir in the DATA_DIR with rel_path."""
#     return create_data_dir(get_rel_path(exper_date, sub_dir))
