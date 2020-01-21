import qgrid
import pandas as pd
import yaml

from pathlib import Path

def grid_from_yaml(yaml_path, df: pd.DataFrame = None):
    with Path(yaml_path).open('r') as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)

    if df is None:
        df = pd.read_pickle(cfg['df'])

    if 'default_columns' in cfg:
        df = df[cfg['default_columns']]

    return qgrid.show_grid(df, **cfg['qgrid'])
