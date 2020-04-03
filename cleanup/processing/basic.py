import logging
from dataclasses import dataclass
from typing import List

import pandas as pd

from . import filter
from .processor import Processor

logger = logging.getLogger(__name__)


@dataclass
class FolderExcluder(Processor):
    folders: List[str]
    path_col: str = 'path'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        m = filter.filter_path(df, self.folders, self.path_col)
        logger.info(f'Excluded files based on their paths'.ljust(self.width) + f'{m.sum()}')
        return df[~m]


@dataclass
class FileIncluder(Processor):
    file_types: List[str]
    path_col: str = 'path'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        m = filter.filter_extension(df, self.file_types, self.path_col)
        logger.info(f'Included files based on ext'.ljust(self.width) + f'{m.sum()}')
        return df[m]


@dataclass
class MinFileSize(Processor):
    min_size: int
    size_col: str = 'st_size'

    def process(self, df: pd.DataFrame, ) -> pd.DataFrame:
        m = df[self.size_col] > self.min_size
        logger.info(f'Above filesize limit'.ljust(self.width) + f'{m.sum()}')
        return df[m]

@dataclass
class ParentCol(Processor):
    path_col:str = 'path'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df['parent'] = df[self.path_col].apply(lambda p: p.parents[0])
        return df