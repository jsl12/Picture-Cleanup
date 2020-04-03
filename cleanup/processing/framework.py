import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import yaml

from .base import BaseFilenameMaker
from .basic import FolderExcluder, MinFileSize, FileIncluder, ParentCol
from .date import DateSelector
from .date import ScanPathDate
from .processor import ConvertIfdTag
from .processor import Processor
from .unique import UniqueIDer

logger = logging.getLogger(__name__)


processor_map = {
    'exclude_folders': FolderExcluder,
    'filesize_min': MinFileSize,
    'include_ext': FileIncluder,
    'duplicate_keys': UniqueIDer,
    'base_filename': BaseFilenameMaker,
    'parent_col': ParentCol,
    'pathdate': ScanPathDate,
    'convert_ifdtag': ConvertIfdTag,
    'select_date': DateSelector
}


@dataclass
class ProcessChain:
    processors: List[Processor]

    @staticmethod
    def from_yaml(yaml_path):
        yaml_path = yaml_path if isinstance(yaml_path, Path) else Path(yaml_path)
        with yaml_path.open('r') as file:
            cfg = yaml.load(file, Loader=yaml.SafeLoader)['processing']

        def make_processor(config):
            processor_key = list(config.keys())[0]
            processor = processor_map[processor_key]
            args = config[processor_key]
            if isinstance(args, dict):
                return processor(**args)
            else:
                return processor(args)

        return ProcessChain([make_processor(p) for p in cfg])

    def process_all(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f'Processing'.ljust(50) + f'{df.shape[0]} files')
        for p in self.processors:
            logger.info(repr(p))
            df = p.process(df)
        logger.info('-' * 70)
        logger.info(f'Total remaining files'.ljust(50) + f'{df.shape[0]}')
        return df
