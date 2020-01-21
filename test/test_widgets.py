import pandas as pd
import yaml

from interface import DupInterface

with open(r'jsl\jsl.yaml', 'r') as file:
    cfg = yaml.load(file, Loader=yaml.SafeLoader)

di = DupInterface(
    pd.DataFrame(),
    qgrid_opts=cfg.get('qgrid', {}),
    default_columns=cfg.get('default_columns', None),
    dup_pre_sel=cfg.get('default_duplicates', None),
    exclude_folders=cfg['exclude_folders'],
    include_ext=cfg['ext']
)