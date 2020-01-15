import os
from pathlib import Path

import pandas as pd

import log
import pic_collections


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


def df_from_dir(source):
    files = [f for f in pic_collections.file_gen(source, ext=None)]
    return pd.DataFrame(data={'path': files})


def df_from_glob(source):
    return pd.DataFrame(data={'path': [f for f in source]})


def add_stats(df):
    stat_df = pd.DataFrame(df['path'].apply(lambda p: extract_stats(os.stat(p))).to_list())
    return pd.concat([df, stat_df], axis=1)


def extract_stats(stat_obj):
    res = {key: getattr(stat_obj, key) for key in dir(stat_obj) if key[:3] == 'st_'}
    return res


if __name__ == '__main__':
    df = csv_copied('jsl_cleanup.log', 'copied files.csv')
