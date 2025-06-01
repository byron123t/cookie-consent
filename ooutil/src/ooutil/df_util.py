"""Pandas util."""

from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Iterable, List, Optional
import json
import random
import yaml

from p_tqdm import p_umap
from tqdm import tqdm
import pandas as pd


from ooutil.file import file_empty


def get_list(adf):
    return list(adf.itertuples(index=False, name=None))


def reader(filepath):
    amap = json.loads(filepath.read_text()) if not file_empty(filepath) else {}
    return amap if amap is not None else {}


def read_jsons_to_df(json_files):
    """Read json files into df."""
    pool = Pool(8)  # number of cores you want to use
    results = []
    results = pool.map(reader, json_files)  # creates a list of the loaded df's
    return pd.DataFrame(results)


def read_jsons_in_dir(adir):
    """Read json files in a directory into df."""
    json_files = list(adir.glob('*.json'))
    print(f'Read {len(json_files)} files.')
    return read_jsons_to_df(json_files)


def find_all(df, col, val):
    return df[df[col] == val]


def find_one_mask(df: pd.DataFrame, mask, keep='last', unique_warning=False):
    """Find one element (last or first) from df with a mask filter."""
    found = df[mask]
    if unique_warning and len(found) != 1:
        print(f"WARNING: Found {len(found)} elements instead of 1.")

    assert keep in ['first', 'last'], f'Invalid {keep=}'
    idx = 0 if keep == 'first' else -1

    return found.iloc[idx] if len(found) > 0 else None


def find_one(df: pd.DataFrame, col, val, keep='last', unique_warning=False):
    """Find the first/last one. Return none if not found."""
    return find_one_mask(df, df[col] == val, keep=keep, unique_warning=unique_warning)


def expand_dict_col(df, dict_col):
    """Expand a dictionary column to columns. May omit some columns :("""
    return df.join(pd.DataFrame(df[dict_col].tolist()), rsuffix='_' + dict_col).drop(dict_col, axis=1)

def expand_key_values_col(df: pd.DataFrame, col_name: str, col_keys: List[str]=None, drop_col=True):
    """Expand key-values columns."""
    if col_keys is not None:
        for key in col_keys:
            df[key] = df[col_name].map(lambda kv: kv.get(key) if not pd.isna(kv) else None)
    if drop_col:
        df = df.drop(columns=[col_name])
    return df


def filter_concat_read(data_files: List[Path], read_func: Callable[[Path], pd.DataFrame], max_n_cpus: int=1):
    """Read data files and concat them.
    read_func accepts 1 argument data_file and read to a DataFrame.
    """
    dfs = p_umap(read_func, data_files, num_cpus=min(max_n_cpus, len(data_files)))
    return filter_concat(dfs)
    # return filter_concat(read_func(data_file) for data_file in data_files)


def filter_concat(dfs: Iterable[Optional[pd.DataFrame]]):
    """Concat maybe-empty-or-none data frames."""
    valid_dfs = [df for df in dfs if df is not None and len(df)> 0]
    return pd.concat(valid_dfs) if len(valid_dfs) > 0 else None


def read_jsonline_to_df(span_file):
    import jsonlines
    with jsonlines.open(span_file) as reader:
        span_dicts = [obj for obj in reader]
    return pd.json_normalize(span_dicts)


def read_data_files(data_files, usecols=None, max_files=0, random_state=1025, add_package_col=False, verbose=0):
    """Read multiple tsv/Excel data files into a single DataFrame."""
    df_list = []
    if max_files > 0:
        data_files = list(data_files)
        num_files = min(max_files, len(data_files))
        random.seed(random_state)
        data_files = random.sample(data_files, num_files)

    if not isinstance(data_files, list):
        data_files = list(data_files)
    for data_file in tqdm(data_files, total=len(data_files)):
        if verbose >= 2:
            print('Reading {}'.format(data_file))
        assert data_file.exists(), '{} not exist'.format(data_file)

        if data_file.suffix == '.tsv':
            df = pd.read_csv(data_file, usecols=usecols, sep='\t')
        elif data_file.suffix == '.csv':
            df = pd.read_csv(data_file, usecols=usecols)
        elif data_file.suffix == '.xlsx':
            df = pd.read_excel(data_file, usecols=usecols)
        elif data_file.suffix == '.json':
            df = pd.read_json(data_file)
            if usecols is not None:
                df = df[usecols]
        elif data_file.suffix == '.jsonl':
            df = read_jsonline_to_df(data_file)
            if usecols is not None:
                df = df[usecols]
        elif data_file.suffix == '.parquet':
            df = pd.read_parquet(data_file)
        else:
            raise ValueError(f'Unsupported file format {data_file}')

        if add_package_col:
            df.insert(0, 'package', [data_file.stem] * len(df))
        df_list.append(df)

    return pd.concat(df_list, axis=0, ignore_index=True)


class LineBreakDumper(yaml.SafeDumper):
    # HACK: insert blank lines between top-level objects
    # inspired by https://stackoverflow.com/a/44284819/3786245
    def write_line_break(self, data=None):
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()

def dump_to_yaml(df: pd.DataFrame, **kwargs):
    return yaml.dump(df.to_dict('records'), Dumper=LineBreakDumper, indent=4, **kwargs)

def write_df_to_file(df: pd.DataFrame, out_file: Path):
    if out_file.suffix == '.csv':
        df.to_csv(out_file)
    elif out_file.suffix == '.tsv':
        df.to_csv(out_file, sep='\t')
    elif out_file.suffix == '.parquet':
        df.to_parquet(out_file, engine="fastparquet")
    elif out_file.suffix == '.json':
        df.to_json(out_file)
    else:
        raise NotImplementedError(f'Not support format {out_file.name}')
    print(f'Written to {out_file}')
