import logging
from dataclasses import dataclass
from typing import List

import pandas as pd

from . import utils

logger = logging.getLogger(__name__)

class PreProcessor:
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


@dataclass
class FolderExcluder(PreProcessor):
    folders: List[str]

    def process(self, df: pd.DataFrame, path_col='path') -> pd.DataFrame:
        return df[~utils.filter_path(df, self.folders, path_col)]


@dataclass
class FileIncluder(PreProcessor):
    file_types: List[str]

    def process(self, df: pd.DataFrame, path_col='path') -> pd.DataFrame:
        return df[utils.filter_extension(df, self.file_types, path_col)]


@dataclass
class MinFileSize(PreProcessor):
    min_size: int

    def process(self, df: pd.DataFrame, size_col='st_size') -> pd.DataFrame:
        return df[df[size_col] > self.min_size]


class OriginalFinder(PreProcessor):
    def process(self, df: pd.DataFrame, path_col='path') -> pd.DataFrame:
        return df
