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

        self.w = 20

        if yaml_path is not None:
            self.yaml_path = yaml_path

    @property
    def unique(self):
        return self.df[self.mask_u]

    @property
    def duplicated(self):
        return self.df[self.mask_d]

    def mark_single_unique(self, index, unique_iloc):
        res = pd.Series(np.zeros(index.shape[0], dtype=bool), index=index)
        res.loc[unique_iloc] = True
        self.mark_unique(res, 'end tree')
        self.mark_duplicate(~res, 'end tree dup')
        return res, ~res

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

    def flat_process(self, keys=['st_size', 'suffix', 'shortname']):
        self.df['suffix'] = self.df['path'].apply(lambda p: p.suffix.upper())
        self.df['shortname'] = self.df['path'].apply(self.transform_filename)
        big_dup = self.df.duplicated(keys, keep=False)
        self.mark_unique(~big_dup, 'not big dups')
        for idx, group in self.df[big_dup].groupby(keys):
            lengths = group['filename'].apply(len)
            if not lengths.duplicated(keep=False).all():
                res = lengths.idxmin()
            else:
                group = group.sort_values('filename', ascending=True)
                res = group.index[0]
            un, dup = self.mark_single_unique(group.index, res)

    def process(self):
        print('Processing'.ljust(self.w) + f'{self.df.shape[0]}')
        self.df['suffix'] = self.df['path'].apply(lambda p: p.suffix.upper())
        self.df['shortname'] = self.df['path'].apply(self.transform_filename)

        col_label = 'unique size'
        self.mark_unique(~self.df.duplicated('st_size', keep=False), col_label)

        print('Duplicate sizes'.ljust(self.w) + f'{(~self.mask_u).sum()}')
        for size, size_group in self.df[~self.mask_u].groupby('st_size'):
            un_size_mask = ~size_group.duplicated('suffix', keep=False)
            col_label = 'unique size/ext'
            self.mark_unique(un_size_mask, col_label)

            for suffix, suffix_group in size_group[~un_size_mask].groupby('suffix'):
                un_shortname_mask = ~suffix_group.duplicated('shortname', keep=False)
                col_label = 'unique size/ext/shortname'
                self.mark_unique(un_shortname_mask, col_label)

                for shortname, shortname_group in suffix_group[~un_shortname_mask].groupby('shortname'):
                    shortname_group['EXIF DateTimeOriginal'] = clean.convert_ifdtag(shortname_group['EXIF DateTimeOriginal'])
                    un_date_mask = ~shortname_group.duplicated('EXIF DateTimeOriginal', keep=False)
                    col_label = 'unique size/ext/shortname/exifdate'
                    self.mark_unique(un_date_mask, col_label)
                    if (~un_date_mask).sum() > 0:
                        df = shortname_group[~un_date_mask]
                        lengths = df['filename'].apply(len)
                        same_length = lengths.duplicated(keep=False).all()
                        if same_length:
                            df = df.sort_values('pathdate', ascending=True)
                            self.mark_single_unique(df.index, df.index[0])
                        else:
                            self.mark_single_unique(lengths.index, lengths.idxmin())

        print('Unique'.ljust(self.w) + f'{self.mask_u.sum()}')
        print('Duplicated'.ljust(self.w) + f'{self.duplicated.shape[0]}')
        self.df['mask_d'] = self.mask_d

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
