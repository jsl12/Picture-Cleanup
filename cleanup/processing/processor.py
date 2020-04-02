import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

import pandas as pd
from exifread.classes import IfdTag

logger = logging.getLogger(__name__)

class Processor:
    width: int = 50

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


@dataclass
class ConvertIfdTag(Processor):
    cols: Tuple[str] = ('Image DateTime', 'EXIF DateTimeOriginal')

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        for c in self.cols:
            if c in df:
                df[c] = df[c].apply(self.convert)
            else:
                print(f'{c} is not in {df.columns}')
        return df

    @staticmethod
    def convert(ifd: IfdTag) -> datetime:
        if isinstance(ifd, IfdTag):
            try:
                return datetime.strptime(ifd.values, '%Y:%m:%d %H:%M:%S')
            except Exception as e:
                pass
        elif isinstance(ifd, datetime):
            return ifd
        return pd.NaT
