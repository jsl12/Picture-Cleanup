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
    source_col: str = 'path'
    res_col: str = 'included_folder'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        m = ~filter.filter_path(df, self.folders, self.source_col)
        logger.info(f'Included files based on their paths'.ljust(self.width) + f'{m.sum()}')
        df[self.res_col] = m
        return df


@dataclass
class FileIncluder(Processor):
    file_types: List[str]
    source_col: str = 'path'
    res_col: str = 'included_filetype'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        m = filter.filter_extension(df, self.file_types, self.source_col)
        logger.info(f'Included files based on ext'.ljust(self.width) + f'{m.sum()}')
        df[self.res_col] = m
        return df


@dataclass
class MinFileSize(Processor):
    min_size: int
    source_col: str = 'st_size'
    res_col: str = 'above_min_filesize'

    def process(self, df: pd.DataFrame, ) -> pd.DataFrame:
        m = df[self.source_col] > self.min_size
        logger.info(f'Above filesize limit'.ljust(self.width) + f'{m.sum()}')
        df[self.res_col] = m
        return df


@dataclass
class ParentCol(Processor):
    source_col:str = 'path'
    res_col: str = 'parent'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.res_col] = df[self.source_col].apply(lambda p: p.parents[0])
        return df
