import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

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
    return stat_df(utils.paths_from_dir_txt(source, ext=None))


def stat_df(source, hash_keys=None, parse_pathdate=True):
    LOGGER.info(f'constructing df from: "{source}"')
    files = [f for f in source]
    df = pd.concat([
        pd.DataFrame(data={'path': files, 'filename': [f.name for f in files]}),
        pd.DataFrame([extract_stats(f) for f in files])
    ], axis=1)

    LOGGER.info(f'hashing indices: {df.shape[0]} files')
    hash_keys = hash_keys or ['filename', 'st_size']
    df.index = pd.Index(
        data=df.apply(lambda row: utils.hash([row[key] for key in hash_keys]), axis=1),
        name='hash'
    )

    LOGGER.info(f'converting timestamps: {df.shape[0]} files')
    for col in df:
        if ('time' in col) and ('_ns' not in col):
            df[col] = pd.to_datetime(df[col].apply(datetime.fromtimestamp))

    LOGGER.info(f'parsing pathdates: {df.shape[0]} files')
    if parse_pathdate:
        df['pathdate'] = df['path'].apply(utils.scan_date)

    return df


def extract_stats(path: Path):
    LOGGER.debug(f'getting os stats: "{path}"')
    stat_obj = Path(path).stat()
    return {key: getattr(stat_obj, key) for key in dir(stat_obj) if key[:3] == 'st_'}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    df = stat_df(Path('temp').glob('**\*.jpg'))
    print(df[['path', 'pathdate']])
