"""Utils to handle result files."""

from pathlib import Path
import itertools


def get_rank_domain(file_stem):
    try:
        rank, domain = file_stem.split('-', 1)
        return rank, domain
    except ValueError as e:
        print(f'Error getting rank and domain: {file_stem=}', e)
        return None


def get_domain(file_stem: Path):
    rank_domain = get_rank_domain(file_stem)
    if rank_domain is None:
        return None
    return rank_domain[1]


def get_domains_of_files_in_dir(data_dir: Path):
    for afile in data_dir.glob('*'):
        if afile.is_file() and not afile.name.startswith('.'):
            yield get_domain(afile)


def get_files_in_dir(adir: Path, file_ext: str, recursive=True, exclude_suffix=None, verbose=0):
    glob_pattern = f'**/*.{file_ext}' if recursive else f'*.{file_ext}'
    files = list(adir.glob(glob_pattern))
    if verbose >= 2: print(f'{glob_pattern=} {adir=}')
    if exclude_suffix is not None:
        files = [f for f in files if not f.stem.endswith(exclude_suffix)]
    return files

def get_files_in_dir_nobottom(adir: Path, file_ext, recursive=True):
    return get_files_in_dir(adir, file_ext, recursive, exclude_suffix='_bottom')


def get_png_files_in_dir_nobottom(adir: Path, recursive=True):
    return get_files_in_dir_nobottom(adir, 'png', recursive)

def get_img_files_in_anno_dir(adir, recursive=True, exclude_suffix='_bottom'):
    files = []
    for file_ext in ['png', 'jpeg']:
        files.extend(get_files_in_dir(adir, file_ext, recursive, exclude_suffix))
    return files

def get_sites_in_anno_dir(adir, recursive=True, exclude_suffix='_bottom'):
    """Assume screenshot files (png and jpeg)."""
    files = get_img_files_in_anno_dir(adir, recursive, exclude_suffix)
    return [f.stem for f in files]


def get_sites_in_anno_dirs(dirs, recursive=True, exclude_suffix='_bottom'):
    return list(itertools.chain.from_iterable(get_sites_in_anno_dir(adir, recursive, exclude_suffix) for adir in dirs))
