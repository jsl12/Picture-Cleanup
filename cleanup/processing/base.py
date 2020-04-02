import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .processor import Processor


@dataclass
class BaseFilenameMaker(Processor):
    path_col:str = 'path'
    base_col:str = 'base'
    match_col:str = 'match'

    def __post_init__(self):
        self.regexes = [
            re.compile('(?P<trim>_ORG)'),
            re.compile('(?P<trim>[abc]? ?(\(\d+\))$)'),
            re.compile('(?P<key>^(PANO|R001|_SC|MVI|CIM|VID|ST\w))(?(key).*)(?P<trim>[-_~]\d{1,3}$)'),
            re.compile('(?P<key>^(DSC|IMG))(?(key).*)(?P<trim>[-_~]\d{1}$)'),
            re.compile('(?P<trim>~\d+)$')
        ]

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = [self.base_col, self.match_col]
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