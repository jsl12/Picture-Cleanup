import logging
from datetime import datetime
from pathlib import Path
from types import GeneratorType

import exifread
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


def stat_df(source,
            parse_pathdate=True,
            min_size=50000,
            ext='all',
            exclude_folders=None,
            os_meta=True,
            exif_meta=False,
            stop_tag=exifread.DEFAULT_STOP_TAG):
    LOGGER.info(f'constructing df from: "{source}"')
    fdf = file_df(source)
    dfs = [fdf]

    if os_meta:
        LOGGER.info(f'reading os stats: {fdf.shape[0]} files')
        dfs.append(pd.DataFrame([extract_stats(f) for f in fdf['path']]))

    if exif_meta:
        LOGGER.info(f'reading exif data: {fdf.shape[0]} files')
        dfs.append(pd.DataFrame([extract_exif(f, stop_tag=stop_tag) for f in fdf['path']]))

    df = pd.concat(dfs, axis=1)

    if min_size is not None:
        df['above min file size'] = df['st_size'] > min_size

    if ext != 'all':
        assert all([isinstance(e, str) for e in ext])
        LOGGER.info(f'checking file extensions: {ext}')
        df['included ext'] = filter_extension(df, ext, 'path')

    if exclude_folders is not None:
        assert all([isinstance(folder, str) for folder in exclude_folders])
        LOGGER.info(f'folder exclusions: {exclude_folders}')
        df['excluded dir'] = filter_path(df, exclude_folders, 'path')

    LOGGER.info(f'converting timestamps: {df.shape[0]} files')
    for col in df:
        if ('time' in col) and ('_ns' not in col):
            df[col] = pd.to_datetime(df[col].apply(datetime.fromtimestamp))

    if parse_pathdate:
        LOGGER.info(f'parsing pathdates: {df.shape[0]} files')
        df['pathdate'] = scan_pathdate(df, 'path')

    return df


def scan_pathdate(df, scan_col='path'):
    return df[scan_col].apply(lambda p: utils.scan_date(p) or pd.NaT)


def file_df(source):
    if isinstance(source, GeneratorType):
        files = [f for f in source]
    elif isinstance(source, Path):
        files = [f for f in source.glob('**\*.*')]
    elif isinstance(source, str):
        files = [f for f in Path(source).glob('**\*.*')]
    return pd.DataFrame(
        data={
            'filename': [f.name for f in files],
            'path': files
        }
    )


def extract_stats(path: Path):
    LOGGER.debug(f'getting os stats: "{path}"')
    stat_obj = Path(path).stat()
    return {key: getattr(stat_obj, key) for key in dir(stat_obj) if key[:3] == 'st_'}


def extract_exif(path: Path, stop_tag=exifread.DEFAULT_STOP_TAG):
    LOGGER.debug(f'getting exif data: "{path}"')
    with Path(path).open('rb') as f:
        return exifread.process_file(f, details=False, stop_tag=stop_tag)


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


def handle_duplicates(df: pd.DataFrame, func, keys=None):
    return df.groupby(keys or ['filename', 'st_size']).apply(func).reset_index(drop=True)


def duplicate_sets(df: pd.DataFrame, keys=None, min=1):
    yield from (
        dup_set                                         # dup_set is a DataFrame
        for (filename, size), dup_set in                # with the groupby object, the iterations will also have the 2 values it is grouping by
        df.groupby(keys or ['filename', 'st_size'])     # group all the sets with unique combinations of values specified by keys
        if dup_set.shape[0] > min                       # only if the set contains more than 1 item
    )


def dupicates_to_file(df: pd.DataFrame, file, keys=None):
    return utils.dfs_to_file(duplicate_sets(df, keys), file)


def res_df(df, target_parent, keep=False, date_col='pathdate'):
    df = df[~df.index.duplicated(keep=keep)]
    df = df[~pd.isnull(df[date_col])]
    df['res'] = df.apply(lambda row: target_parent / row[date_col].strftime('%Y') / row[date_col].strftime('%m %B') / row['filename'], axis=1)
    df['rel'] = df['res'].apply(lambda p: p.relative_to(target_parent))
    return df[['rel', 'path']]


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    df = stat_df(
        source=Path('temp'),
        exclude_folders=['FFF'],
        ext=['.jpg']
    )
    print(df[['path', 'pathdate']])
