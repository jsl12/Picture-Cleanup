import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import yaml

from . import utils

logger = logging.getLogger(__name__)


class PreProcessor:
    width: int = 50

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


@dataclass
class PreProcessFramework:
    pre_processors: List[PreProcessor]

    @staticmethod
    def from_yaml(yaml_path):
        yaml_path = yaml_path if isinstance(yaml_path, Path) else Path(yaml_path)
        with yaml_path.open('r') as file:
            cfg = yaml.load(file, Loader=yaml.SafeLoader)

        objs = []

        if 'exclude_folders' in cfg:
            objs.append(FolderExcluder(cfg['exclude_folders']))

        if 'include_ext' in cfg:
            objs.append(FileIncluder(cfg['include_ext']))

        if 'filesize_min' in cfg:
            objs.append(MinFileSize(cfg['filesize_min']))

        return PreProcessFramework(pre_processors=objs)

    def process_all(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f'Beginning pre-processing of {df.shape[0]} files')
        for p in self.pre_processors:
            logger.info(type(p))
            df = p.process(df)
        logger.info('-' * 70)
        logger.info(f'Total remaining files'.ljust(50) + f'{df.shape[0]}')
        return df


@dataclass
class FolderExcluder(PreProcessor):
    folders: List[str]
    path_col: str = 'path'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        m = utils.filter_path(df, self.folders, self.path_col)
        logger.info(f'Excluded files based on their paths'.ljust(self.width) + f'{m.sum()}')
        return df[~m]


@dataclass
class FileIncluder(PreProcessor):
    file_types: List[str]
    path_col: str = 'path'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        m = utils.filter_extension(df, self.file_types, self.path_col)
        logger.info(f'Included files based on ext'.ljust(self.width) + f'{m.sum()}')
        return df[m]


@dataclass
class MinFileSize(PreProcessor):
    min_size: int
    size_col: str = 'st_size'

    def process(self, df: pd.DataFrame, ) -> pd.DataFrame:
        m = df[self.size_col] > self.min_size
        logger.info(f'Above filesize limit'.ljust(self.width) + f'{m.sum()}')
        return df[m]


class OriginalFinder(PreProcessor):
    def process(self, df: pd.DataFrame, path_col='path') -> pd.DataFrame:
        return df
