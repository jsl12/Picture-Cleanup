import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import check
import log
import utils

LOGGER = logging.getLogger(__name__)


def df_copied(logfile):
    sources, destinations = [list(i) for i in zip(*log.copied_files(logfile))]
    return pd.DataFrame(
        data={
            'source': sources,
            'destination': destinations
        }
    )


def df_errors(logfile):
    paths, error_lines = [list(i) for i in zip(*log.errors(logfile))]
    return pd.DataFrame(
        data={
            'file': paths,
            'error line': error_lines
        }
    )


def csv_copied(logfile, csv_path):
    df = df_copied(logfile)
    df.to_csv(csv_path, index=False)
    return df


def df_from_dir_texts(source):
    files = [f for f in check.paths_from_dir_txt(source)]
    return pd.DataFrame(
        data={
            'path': files,
            'filename': [f.name for f in files]
        }
    )


def stat_df(source, hash=False, hash_keys=None, parse_pathdate=True, ext='all', exclude_folders=None):
    LOGGER.info(f'constructing df from: "{source}"')
    files = [f for f in Path(source).glob('**\*.*')]
    df = pd.concat([
        pd.DataFrame(data={'path': files, 'filename': [f.name for f in files]}),
        pd.DataFrame([extract_stats(f) for f in files])
    ], axis=1)

    master_mask = pd.Series(
        data=np.ones(df.shape[0], dtype=bool),
        index=df.index
    )

    if ext != 'all':
        assert all([isinstance(e, str) for e in ext])
        LOGGER.info(f'checking file extensions: {ext}')
        ext_mask = filter_extension(df, ext, 'path')
        master_mask &= ext_mask

    if exclude_folders is not None:
        assert all([isinstance(folder, str) for folder in exclude_folders])
        LOGGER.info(f'folder exclusions: {exclude_folders}')
        exc_mask = filter_path(df, exclude_folders, 'path')
        master_mask &= exc_mask

    df, rejects = df[master_mask], df[~master_mask]

    LOGGER.info(f'converting timestamps: {df.shape[0]} files')
    for col in df:
        if ('time' in col) and ('_ns' not in col):
            df[col] = pd.to_datetime(df[col].apply(datetime.fromtimestamp))

    if parse_pathdate:
        LOGGER.info(f'parsing pathdates: {df.shape[0]} files')
        df['pathdate'] = df['path'].apply(lambda p: utils.scan_date(p) or pd.NaT)

    if hash:
        df = hash_index(df, hash_keys)
    return df, rejects


def extract_stats(path: Path):
    LOGGER.debug(f'getting os stats: "{path}"')
    stat_obj = Path(path).stat()
    return {key: getattr(stat_obj, key) for key in dir(stat_obj) if key[:3] == 'st_'}


def filter_extension(df, ext, path_col='path'):
    return pd.DataFrame(data={e: df[path_col].apply(lambda p: p.suffix.upper()) == e.upper() for e in ext}).any(axis=1)


def filter_path(df, exc, path_col='path'):
    return pd.DataFrame(data={folder: df[path_col].apply(lambda p: folder.upper() in str(p).upper()) for folder in exc}).any(axis=1)


def hash_index(df, hash_keys=None):
    LOGGER.info(f'hashing indices: {df.shape[0]} files')
    hash_keys = hash_keys or ['filename', 'st_size']
    df.index = pd.Index(
        data=df.apply(lambda row: utils.hash([row[key] for key in hash_keys]), axis=1),
        name='hash'
    )
    return df


def duplicate_sets(df: pd.DataFrame, keys=None):
    keys = keys or ['filename', 'st_size']
    yield from (df[(df[keys] == row[keys]).all(axis=1)] for hash, row in df[df.duplicated(keys, keep=False)].iterrows())


def dupicates_to_file(df: pd.DataFrame, file, keys=None):
    return utils.dfs_to_file([df for idx, df in df.groupby(keys or ['filename', 'st_size']) if df.shape[0] > 1], file)


def res_df(df, target_parent, keep=False, date_col='pathdate'):
    df = df[~df.index.duplicated(keep=keep)]
    df = df[~pd.isnull(df[date_col])]
    df['res'] = df.apply(lambda row: target_parent / row[date_col].strftime('%Y') / row[date_col].strftime('%m %B') / row['filename'], axis=1)
    df['rel'] = df['res'].apply(lambda p: p.relative_to(target_parent))
    return df[['rel', 'path']]


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    df, rejects = stat_df(
        source=Path('temp'),
        exclude_folders=['FFF'],
        ext=['.jpg']
    )
    print(df[['path', 'pathdate']])
