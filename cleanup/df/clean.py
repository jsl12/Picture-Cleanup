from datetime import datetime

import pandas as pd
import yaml
from exifread import IfdTag


def convert_ifdtag(col):
    def conv(val):
        if pd.isnull(val):
            return pd.NaT
        if isinstance(val, IfdTag):
            return datetime.strptime(val.values, '%Y:%m:%d %H:%M:%S')
        else:
            return val

    return col.apply(conv)

if __name__ == '__main__':
    with open(r'C:\Users\lanca_000\Documents\Software\Python\Picture Cleanup\jsl\jsl.yaml', 'r') as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)
        df = pd.read_pickle(cfg['df'])
    convert_ifdtag(df['EXIF DateTimeOriginal'])
