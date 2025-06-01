"""File util."""

from datetime import datetime, timedelta
from pathlib import Path



def file_empty(afile: Path):
    return afile.stat().st_size == 0


def file_old(afile: Path):
    # return datetime.fromtimestamp(afile.stat().st_ctime) < datetime.now() - timedelta(seconds=120)
    return datetime.fromtimestamp(afile.stat().st_ctime) < datetime.now() - timedelta(seconds=300)


def file_empty_and_old(afile: Path):
    assert afile.exists(), f'{afile=} not exist.'
    return file_empty(afile) and file_old(afile)


def add_second_suffix(apath: Path, second_suffix: str):
    assert second_suffix.startswith('.'), f'{second_suffix} does not start with a dot'
    return apath.with_suffix(second_suffix + apath.suffix)


def next_path(path_pattern) -> Path:
    # From https://stackoverflow.com/questions/17984809/how-do-i-create-an-incrementing-filename-in-python
    # Use naive approach to verify its correctness.
    """
    Finds the next free path in an sequentially named list of files.

    e.g. path_pattern = 'file-%s.txt':

    file-1.txt
    file-2.txt
    file-3.txt

    Naive (slow) version of next_path
    """
    i = 0
    while Path(path_pattern % i).exists():
        i += 1
    return Path(path_pattern % i)

def get_next_path(apath: Path, suffix_pattern=r".%s", verbose=0) -> Path:
    assert r'%s' in suffix_pattern, f'{suffix_pattern} must contain %s'

    path_pattern = add_second_suffix(apath, suffix_pattern)
    if verbose >= 2: print(f"get next path {path_pattern=}")
    return next_path(str(path_pattern))

# def file_exists_not_empty_and_old(afile: Path):
    # return afile.exists() and not file_empty_and_old(afile)
    # return afile.exists() and not file_empty(afile) and not file_old(afile)

def test():
    apath = Path("/a/b.json")
    print(add_second_suffix(apath, ".bg.0"))
    print(add_second_suffix(apath, r".%s"))

if __name__ == '__main__':
    test()