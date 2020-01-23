import logging
from datetime import datetime
from pathlib import Path
from types import GeneratorType

import exifread
import pandas as pd

from .utils import scan_pathdate, read_os_stats, read_exif, filter_extension, filter_path

LOGGER = logging.getLogger(__name__)


def stat_df(source,
            keep_cols=None,
            parse_pathdate=True,
            min_size=50000,
            ext='all',
            exclude_folders=None,
            os_meta=True,
            exif_meta=False,
            suffix_col=True,
            unique_size_col=False,
            stop_tag=exifread.DEFAULT_STOP_TAG):
    LOGGER.info(f'constructing df from: "{source}"')

    df = file_df(source)
    if df is None:
        return pd.DataFrame()

    if exclude_folders is not None:
        assert all([isinstance(folder, str) for folder in exclude_folders])
        LOGGER.info(f'folder exclusions: {exclude_folders}')
        df['excluded dir'] = filter_path(df, exclude_folders, 'path')

    if ext != 'all':
        assert all([isinstance(e, str) for e in ext])
        LOGGER.info(f'checking file extensions: {ext}')
        df['included ext'] = filter_extension(df, ext, 'path')

    dfs = [df]

    if os_meta:
        LOGGER.info(f'reading os stats: {df.shape[0]} files')
        dfs.append(pd.DataFrame([read_os_stats(f) for f in df['path']]))

    if exif_meta:
        LOGGER.info(f'reading exif data: {df.shape[0]} files')
        dfs.append(pd.DataFrame([read_exif(f, stop_tag=stop_tag) for f in df['path']]))

    df = pd.concat(dfs, axis=1)

    if min_size is not None:
        df['above min file size'] = df['st_size'] > min_size

    LOGGER.info(f'converting timestamps: {df.shape[0]} files')
    for col in df:
        if ('time' in col) and ('_ns' not in col):
            df[col] = pd.to_datetime(df[col].apply(datetime.fromtimestamp))

    if parse_pathdate:
        LOGGER.info(f'parsing pathdates: {df.shape[0]} files')
        df['pathdate'] = scan_pathdate(df, 'path')

    if keep_cols is not None:
        df = df[keep_cols]

    if suffix_col:
        df['file type'] = df['path'].apply(lambda p: p.suffix)

    if unique_size_col:
        df['unique size'] = ~df.duplicated('st_size', keep=False)

    return df


def file_df(source):
    try:
        if isinstance(source, GeneratorType):
            files = [f for f in source]
        elif isinstance(source, Path):
            files = [f for f in source.glob('**\*.*')]
        elif isinstance(source, str):
            files = [f for f in Path(source).glob('**\*.*')]
    except OSError as e:
        LOGGER.exception(repr(e))
    else:
        return pd.DataFrame(
            data={
                'filename': [f.name for f in files],
                'path': files
            }
        )