from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .df import utils, clean
from .interface.grid import grid_from_yaml


class SizeSorter:
    @staticmethod
    def from_yaml(yaml_path, df: pd.DataFrame = None):
        with Path(yaml_path).open('r') as file:
            cfg = yaml.load(file, Loader=yaml.SafeLoader)

        if df is None:
            df = pd.read_pickle(cfg['df'])

        if 'default_columns' in cfg:
            df = df[cfg['default_columns']]

        mask = pd.Series(np.ones(df.shape[0], dtype=bool))

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

        return SizeSorter(df[mask], yaml_path=yaml_path)

    def __init__(self, df: pd.DataFrame, yaml_path=None):
        self.df = df.copy()
        self.df.index = pd.RangeIndex(stop=df.shape[0])
        self.mask_u = pd.Series(np.zeros(df.shape[0], dtype=bool), index=self.df.index)
        self.mask_d = self.mask_u.copy()

        if yaml_path is not None:
            self.yaml_path = yaml_path

    @property
    def unique(self):
        return self.df[self.mask_u]

    @property
    def duplicated(self):
        return self.df[self.mask_d]

    def mark_unique(self, input_mask, name=None):
        self.mark_mask(input_mask, 'mask_u', save_name=name)
        self.save_mask(input_mask, 'mask_u')

    def mark_duplicate(self, input_mask, name=None):
        self.mark_mask(input_mask, 'mask_d', save_name=name)
        self.save_mask(input_mask, 'mask_d')

    def mark_mask(self, input_mask, mask_name, save_name=None):
        if save_name is not None:
            self.save_mask(input_mask, save_name)
        if hasattr(self, mask_name):
            getattr(self, mask_name)[input_mask.index] = input_mask

    def save_mask(self, mask: pd.Series, name:str):
        if name not in self.df:
            self.df[name] = pd.Series(np.zeros(self.df.shape[0], dtype=bool), index=self.df.index)
        self.df.loc[mask.index, name] = mask

    def process(self, size_col='st_size', **kwargs):
        self.w = 20
        print('Processing'.ljust(self.w) + f'{self.df.shape[0]}')

        self.unique_size = ~self.df.duplicated(size_col, keep=False)
        self.mark_unique(self.unique_size, 'unique size')

        self.df[~self.mask_u].groupby(size_col).apply(self.process_size_group, **kwargs)

        print('Unique'.ljust(self.w) + f'{self.mask_u.sum()}')
        print('Duplicated'.ljust(self.w) + f'{self.duplicated.shape[0]}')

    def process_size_group(self, df: pd.DataFrame, path_col='path', **kwargs):
        df['suffix'] = df[path_col].apply(lambda p: p.suffix.upper())

        # find unique extensions and mark them as unique overall
        unique_ext = ~df.duplicated('suffix', keep=False)
        self.mark_unique(unique_ext, 'unique size/ext combo')

        remaining = ~unique_ext
        df = df[remaining]

        if remaining.sum() > 0:
            df['shortname'] = df['path'].apply(self.transform_filename)
            unique_shortname = ~df.duplicated('shortname', keep=False)
            self.mark_unique(unique_shortname, 'unique shortname')

            remaining = ~unique_shortname
            df = df[remaining]

            if remaining.sum() > 0:
                df.groupby('shortname').apply(self.process_short_names, **kwargs)

    def process_short_names(self, df: pd.DataFrame, path_col='path', **kwargs):
        df['EXIF DateTimeOriginal'] = clean.convert_ifdtag(df['EXIF DateTimeOriginal'])
        unique_exifdate = ~df.duplicated('EXIF DateTimeOriginal', keep=False)
        self.mark_unique(unique_exifdate, 'unique exif date')

        remaining = ~unique_exifdate
        df = df[remaining]

        if remaining.sum() > 0:
            df = df.sort_values('filename')
            self.mark_unique(
                pd.Series(
                    [True],
                    index=[df.index[0]]
                ),
                'first filename'
            )
            self.mark_duplicate(
                pd.Series(
                    np.ones(len(df.index[1:]), dtype=bool),
                    index=df.index[1:]
                ),
                'not first filename'
            )


    @staticmethod
    def transform_filename(path: Path) -> str:
        # path.stem is the filename without the extension
        res: str = path.stem
        try:
            # try to parse the first 8 chars as YYYYMMDD
            date = datetime.strptime(res[:8], '%Y%m%d')
        except Exception:
            # if any error happens, no problem, just keep going
            pass
        else:
            # only if it was successful (no exceptions raised), return the first 15 chars
            return res[:15]

        # check if the ASCII number of the first 3 chars of res are letters
        if res[:3].isalpha():
            return res[:8]

        # if it makes it down here, just return the whole stem
        return res

    def grid(self, yaml_path=None):
        if yaml_path is not None:
            self.yaml_path = yaml_path

        if hasattr(self, 'yaml_path'):
            return grid_from_yaml(self.yaml_path, self.df)
        else:
            print(f'SizeSorter has no yaml_path attribute to use')
