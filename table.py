import os
from pathlib import Path

import pandas as pd

import log
import pic_collections
import utils


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
    return stat_df(pic_collections.file_gen(source, ext=None))


def stat_df(source, hash_keys=None):
    files = [f for f in source]
    df = pd.concat([
        pd.DataFrame(data={'path': files, 'filename': [f.name for f in files]}),
        pd.DataFrame([extract_stats(os.stat(f)) for f in files])
    ], axis=1)

    hash_keys = hash_keys or ['filename', 'st_size']
    if hash_keys is not None:
        df.index = df.apply(lambda row: utils.hash([row[key] for key in hash_keys]), axis=1)
    return df


def extract_stats(stat_obj):
    return {key: getattr(stat_obj, key) for key in dir(stat_obj) if key[:3] == 'st_'}


if __name__ == '__main__':
    df = csv_copied('jsl_cleanup.log', 'copied files.csv')
