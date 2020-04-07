import logging
from dataclasses import dataclass
from typing import Iterable, List

import pandas as pd

from .processor import Processor
from .. import utils

logger = logging.getLogger(__name__)


@dataclass
class UniqueIDer(Processor):
    mask_cols: List[str]
    source_cols: List[str]
    priority_keyword: List[str] = None
    w:int = 35

    @utils.timer
    def process(self, df: pd.DataFrame):
        logger.info('Creating new columns')
        df['unique'] = False
        df['duplicated'] = False
        df['reason'] = ''

        if len(self.mask_cols) > 0:
            logger.info(f"Applying 'continue' mask")
            process_df = df[df[self.mask_cols].all(axis=1)].sort_values('path', ascending=False)

        logger.info('Calculating duplicates')
        dups = process_df.duplicated(self.source_cols, keep=False)
        df.loc[process_df[dups].index, 'duplicated'] = True
        df.loc[process_df[~dups].index, 'unique'] = True
        logger.info(f'{(~dups).sum()} unique, {dups.sum()} duplicate')

        logger.info(f'Processing groups of duplicates')
        grouped = process_df[dups].groupby(self.source_cols)
        logger.info(f'{grouped.ngroups} groups, {grouped.size().mean():.1f} avg files')
        for idx, group in grouped:
            i, reason = self.select_index(group)
            df.loc[i, 'unique'] = True
            df.loc[i, 'reason'] = reason

        logger.info(f'{df["unique"].sum()} total unique files')
        return df

    def select_index(self, group: pd.DataFrame):
        """
        Selects a single integer index from a DataFrame

        :param group: DataFrame to select the index from
        :param priority_keyword: Prioritizes paths with this keyword in them
        :return: int index
        """
        # If there's a priority_keyword
        if self.priority_keyword is not None:
            if isinstance(self.priority_keyword, Iterable):
                lr = group['path'].apply(str).str.contains('|'.join(self.priority_keyword), case=False)
            else:
                # Check to see if it shows up in any of the paths
                lr = group['path'].apply(lambda p: self.priority_keyword in str(p))

            if lr.any():
                # If so, return the index of the first path it shows up in
                return group[lr].index[0], 'priority'
        return group.index[0], 'first in list'
