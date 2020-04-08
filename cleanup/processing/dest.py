from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .processor import Processor


@dataclass
class DestinationGenerator(Processor):
    dest_base: str
    res_col: str = 'dest'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.res_col] = df.apply(self.gen_dest, axis=1)
        return df

    def gen_dest(self, row: pd.Series) -> Path:
        return Path(self.dest_base) / row['path'].name

@dataclass
class DatedDestinationGen(DestinationGenerator):
    format:str = r'%Y\%m %b'
    def gen_dest(self, row: pd.Series) -> Path:
        return Path(self.dest_base) / row['selected_date'].strftime(self.format) / row['path'].name
