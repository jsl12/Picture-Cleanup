from datetime import datetime

import pandas as pd
import yaml
from exifread import IfdTag


def convert_datetime(val):
    if pd.isnull(val):
        return pd.NaT
    if isinstance(val, IfdTag):
        try:
            return datetime.strptime(val.values, '%Y:%m:%d %H:%M:%S')
        except ValueError:
            return pd.NaT
    elif isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    else:
        raise ValueError(val)

def convert_ifdtag(col):
    return col.apply(convert_datetime)

if __name__ == '__main__':
    with open(r'C:\Users\lanca_000\Documents\Software\Python\Picture Cleanup\jsl\jsl.yaml', 'r') as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)
        df = pd.read_pickle(cfg['df'])
    convert_ifdtag(df['EXIF DateTimeOriginal'])
