import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import yaml

from . import utils

logger = logging.getLogger(__name__)


class PreProcessor:
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
        for p in self.pre_processors:
            df = p.process(df)
        return df


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
