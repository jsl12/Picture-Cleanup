import logging
from datetime import datetime
from pathlib import Path
from types import GeneratorType

import exifread
import pandas as pd
import yaml

from .utils import read_os_stats, read_exif, timer

LOGGER = logging.getLogger(__name__)

@timer
def stat_df_yaml(source, yaml_path, **kwargs):
    with Path(yaml_path).open('r') as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)

    if 'filesize_min' in cfg:
        kwargs['min_size'] = cfg['filesize_min']

    if 'default_columns' in cfg:
        kwargs['keep_cols'] = cfg['keep_cols']

    res = stat_df(source, **kwargs)

    return res

def stat_df(source,
            keep_cols=None,
            min_size=50000,
            os_meta=True,
            exif_meta=False,
            stop_tag=exifread.DEFAULT_STOP_TAG):
    LOGGER.info(f'constructing df from: "{source}"')

    df = file_df(source)
    if df is None:
        return pd.DataFrame()

    df = df.reset_index(drop=True)
    dfs = [df]

    if os_meta:
        LOGGER.info(f'reading os stats: {df.shape[0]} files')
        dfs.append(pd.DataFrame([read_os_stats(f) for f in df['path']]))

    if exif_meta:
        LOGGER.info(f'reading exif data: {df.shape[0]} files')
        dfs.append(pd.DataFrame([read_exif(f, stop_tag=stop_tag) for f in df['path']]))

    df = pd.concat(dfs, axis=1)

    if min_size is not None:
        df = df[df['st_size'] > min_size]

    LOGGER.info(f'converting timestamps: {df.shape[0]} files')
    for col in df:
        if ('time' in col) and ('_ns' not in col):
            df[col] = pd.to_datetime(df[col].apply(datetime.fromtimestamp))

    if keep_cols is not None:
        df = df[keep_cols]

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
