import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import yaml

from .basic import FolderExcluder, MinFileSize, FileIncluder
from .processor import Processor

logger = logging.getLogger(__name__)


@dataclass
class ProcessChain:
    processors: List[Processor]

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

        return ProcessChain(pre_processors=objs)

    def process_all(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f'Beginning pre-processing of {df.shape[0]} files')
        for p in self.processors:
            logger.info(type(p))
            df = p.process(df)
        logger.info('-' * 70)
        logger.info(f'Total remaining files'.ljust(50) + f'{df.shape[0]}')
        return df
