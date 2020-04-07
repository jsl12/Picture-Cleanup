import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd

from .processor import Processor


@dataclass
class BaseFilenameMaker(Processor):
    regexes: List[str]
    path_col:str = 'path'
    res_col:str = 'base'
    match_col:str = 'match'

    def __post_init__(self):
        self.regexes = [re.compile(r, re.IGNORECASE) for r in self.regexes]

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = [self.res_col, self.match_col]
        vals = df[self.path_col].apply(self.convert_base_filename, regexes=self.regexes)
        df[cols] = pd.DataFrame(data=vals.to_list(), index=df.index)
        return df

    @staticmethod
    def convert_base_filename(path: Path, regexes) -> str:
        filename = path.stem
        trim = ''
        for rgx in regexes:
            m = rgx.search(filename)
            if m is not None:
                filename = filename[:m.start('trim')] + filename[m.end('trim'):]
                trim += m.group('trim')
        return filename, trim if trim != '' else None