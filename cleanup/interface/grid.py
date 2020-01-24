from pathlib import Path

import numpy as np
import pandas as pd
import qgrid
import yaml

from ..df import utils


def grid_from_yaml(yaml_path, df: pd.DataFrame = None):
    with Path(yaml_path).open('r') as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)

    if df is None:
        df = pd.read_pickle(cfg['df'])

    if 'default_columns' in cfg:
        df = df[cfg['default_columns']]

    mask = pd.Series(np.ones(df.shape[0], dtype=bool), index=df.index)

    if 'exclude_folders' in cfg:
        exc = utils.filter_path(df, cfg['exclude_folders'])
        print(f'Skipping {exc.sum()} files for excluded folders')
        mask &= ~exc

    if 'include_ext' in cfg:
        inc = utils.filter_extension(df, cfg['include_ext'])
        print(f'Including {inc.sum()} files because of extensions')
        mask &= inc

    if 'filesize_min' in cfg:
        size = df['st_size'] >= cfg['filesize_min']
        print(f'Skipping {(~size).sum()} files because of size')
        mask &= size

    return qgrid.show_grid(df[mask], **cfg['qgrid'])
