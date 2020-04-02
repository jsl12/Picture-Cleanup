from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import utils


class UniqueIDer:
    w = 35
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.index = pd.RangeIndex(stop=df.shape[0])
        self.mask_u = pd.Series(np.zeros(df.shape[0], dtype=bool), index=self.df.index)
        self.mask_d = self.mask_u.copy()

    @property
    def unique(self) -> pd.DataFrame:
        return self.df[self.mask_u]

    @property
    def duplicated(self) -> pd.DataFrame:
        return self.df[self.mask_d]

    def mark_single_unique(self, index: pd.Index, unique_loc: int):
        """
        Wrapper to ensure that only a single file gets marked as unique

        :param index:
        :param unique_loc:
        :return:
        """
        # Create a new boolean Series with the same index
        res = pd.Series(np.zeros(index.shape[0], dtype=bool), index=index)

        # Set a single location to True
        res.loc[unique_loc] = True

        # Mark the master unique Series with the mask
        self.mark_unique(res, 'unique from group')

        # Mark the master duplicate Series with the inverse of that mask
        self.mark_duplicate(~res, 'dup from group')
        return res, ~res

    def mark_unique(self, input_mask, name=None):
        self.mark_mask(input_mask, 'mask_u', save_name=name or 'mask_u')

    def mark_duplicate(self, input_mask, name=None):
        self.mark_mask(input_mask, 'mask_d', save_name=name or 'mask_d')

    def mark_mask(self, input_mask, mask_name, save_name=None):
        """
        Generic function for marking positions of one of the mask attributes of the UniqueIDer

        :param input_mask:
        :param mask_name:
        :param save_name:
        :return:
        """
        if save_name is not None:
            self.save_mask(input_mask, save_name)
        if hasattr(self, mask_name):
            getattr(self, mask_name)[input_mask.index] = input_mask

    def save_mask(self, mask: pd.Series, name:str):
        """
        Sets a column in the DataFrame (self.df) with the name argument to the values in the mask argument

        :param mask: Series of indices, values to set
        :param name: Name of column in self.df
        :return: None
        """
        if name not in self.df:
            self.df[name] = pd.Series(np.zeros(self.df.shape[0], dtype=bool), index=self.df.index)
        self.df.loc[mask.index, name] = mask

    @utils.timer
    def process(self, keys=None, *args, **kwargs):
        print('Calculating duplicates'.ljust(self.w), end='')
        big_dup = self.df.duplicated(keys, keep=False)
        self.mark_unique(~big_dup, f'not dup: {", ".join(list(keys))}')
        print(f'{(~big_dup).sum()} unique, {big_dup.sum()} duplicate')

        print(f'Processing groups of duplicates'.ljust(self.w), end='')
        grouped = self.df[big_dup].groupby(keys)
        print(f'{grouped.ngroups} groups, {grouped.size().mean():.1f} avg files')
        for idx, group in grouped:
            i = self.select_index(group, *args, **kwargs)
            unique, duplicate = self.mark_single_unique(index=group.index, unique_loc=i)

        print('Unique'.ljust(self.w) + f'{self.mask_u.sum()}')
        print('Duplicated'.ljust(self.w) + f'{self.mask_d.sum()}')

    def select_index(self, group: pd.DataFrame, priority_keyword=None) -> int:
        """
        Selects a single integer index from a DataFrame

        :param group: DataFrame to select the index from
        :param priority_keyword: Prioritizes paths with this keyword in them
        :return: int index
        """
        # If there's a priority_keyword
        if priority_keyword is not None:
            # Check to see if it shows up in any of the paths
            lr = group['path'].apply(lambda p: priority_keyword in str(p))
            if lr.any():
                # If so, return the index of the first path it shows up in
                return lr[lr].index[0]
        return group.index[0]

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
