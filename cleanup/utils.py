import functools
import logging
import time
from datetime import timedelta
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from .df.clean import convert_datetime

LOGGER = logging.getLogger(__name__)


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        print(f'Finished {func.__name__!r} in {timedelta(seconds=time.perf_counter() - start)}')
        return res
    return wrapper

def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        res = path.with_name(f'{path.stem}({len(files)}){path.suffix}')
        LOGGER.debug(f'unique filepath: "{res}"')
        return res
    else:
        return path


def remove_empty_dirs(base):
    to_remove = []
    for folder in base.glob('**\*'):
        if folder.is_dir():
            contents = [p for p in folder.iterdir()]
            if len(contents) == 0:
                to_remove.append(folder)
    for d in to_remove:
        d.rmdir()


def dfs_to_file(df_list, file):
    with Path(file).open('w') as f:
        for df in df_list:
            f.write(('-' * 50) + '\n')
            for idx, row in df.iterrows():
                f.write('    '.join([
                    str(row["pathdate"].date()),
                    str(row["filename"]),
                    f'{row["st_size"] / 1000:.2f} kB',
                    str(row["path"])
                ]) + '\n')


def paths_from_dir_txt(path, ext='jpg'):
    path = Path(path)
    for file in path.glob('*.txt'):
        with file.open('r') as f:
            line = True
            while line:
                line = f.readline()
                try:
                    p = Path(line.strip())
                except Exception as e:
                    continue
                else:
                    if ext is not None and p.suffix == f'.{ext}':
                        yield p
                    elif ext is None and p.suffix != '':
                        yield p


def df_from_dir_texts(source):
    files = [f for f in check.paths_from_dir_txt(source)]
    return pd.DataFrame(
        data={
            'path': files,
            'filename': [f.name for f in files]
        }
    )


def duplicate_sets(df: pd.DataFrame, keys=None, min=1):
    yield from (
        dup_set                                         # dup_set is a DataFrame
        for idx, dup_set in                # with the groupby object, the iterations will also have the 2 values it is grouping by
        df.groupby(keys or ['filename', 'st_size'])     # group all the sets with unique combinations of values specified by keys
        if dup_set.shape[0] > min                       # only if the set contains more than 1 item
    )


def dupicates_to_file(df: pd.DataFrame, file, keys=None):
    return utils.dfs_to_file(duplicate_sets(df, keys), file)


def gen_result_df(result_source, target_folder=None, exclude_path=None, include_suffix=None, path_gen=None):
    if isinstance(result_source, str):
        result_source = Path(result_source)

    if isinstance(result_source, pd.DataFrame):
        df = result_source
    elif isinstance(result_source, Path) and result_source.is_dir():
        df = pd.concat([
            pd.read_pickle(f) for f in result_source.glob('*.pkl')
        ], sort=False)
    elif result_source.exists() and result_source.suffix == '.pkl':
        df = pd.read_pickle(result_source)
    else:
        raise ValueError(result_source)
    df.index = pd.RangeIndex(stop=df.shape[0])

    mask = pd.Series(np.ones(df.shape[0], dtype=bool), index=df.index)

    if exclude_path is not None:
        mask_exclude_folders = filter_path(df=df, exclude_list=[exclude_path] if not isinstance(exclude_path, list) else exclude_path)
        mask &= ~mask_exclude_folders

    if include_suffix is not None:
        mask_include_suffix = filter_extension(df=df, include_list=[include_suffix] if not isinstance(include_suffix, list) else include_suffix)
        mask &= mask_include_suffix

    df = df[mask]

    df['pathdate'] = df.apply(select_date, axis=1)

    if target_folder is None:
        target_folder = Path.cwd()
    if path_gen is None:
        path_gen = flat_path_gen
    df['target'] = df.apply(lambda row: Path(target_folder) / path_gen(row), axis=1)

    res = pd.DataFrame(
        data={
            'original path': df['path'],
            'target path': df['target'],
            'target parent': df['target'].apply(lambda p: p.parents[0])
        }
    )
    return res

def select_date(row: pd.Series):
    keys = [
        'Image DateTime',
        'EXIF DateTimeOriginal',
        'pathdate'
    ]
    try:
        for key in keys:
            date = convert_datetime(row[key])
            if not pd.isnull(date):
                break
        else:
            return pd.NaT
    except Exception:
        return pd.NaT
    else:
        return date

def flat_path_gen(row, format='%Y-%m-%d'):
    date = row['pathdate']
    if pd.isnull(date):
        return '0000-00-00'
    else:
        try:
            return Path(date.strftime(format))  / row['path'].name
        except Exception as e:
            raise e

def filter_extension(df, include_list, path_col='path'):
    return pd.DataFrame(data={e: df[path_col].apply(lambda p: p.suffix.upper()) == e.upper() for e in include_list}).any(axis=1)


def filter_path(df: pd.DataFrame, exclude_list: List[str], path_col: str = 'path') -> pd.Series:
    return pd.DataFrame(data={folder: df[path_col].apply(str).str.contains(folder, case=False) for folder in exclude_list}).any(axis=1)