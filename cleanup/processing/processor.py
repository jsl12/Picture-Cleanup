import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List

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
    formats: Tuple[str] = ('%Y:%m:%d', '%d/%m/%Y', '%Y_%m_%d')

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        for c in self.cols:
            if c in df:
                df[c] = df[c].apply(self.convert, formats=self.formats)
            else:
                print(f'{c} is not in {df.columns}')
        return df

    @staticmethod
    def convert(ifd: IfdTag, formats:List[str]) -> datetime:
        if isinstance(ifd, IfdTag):
            s = ifd.values.split(' ')[0]
            for fmt in formats:
                try:
                    res = datetime.strptime(s, fmt)
                    break
                except ValueError as e:
                    continue
            else:
                res = pd.NaT

            try:
                if res.year > 2100:
                    return pd.NaT
                else:
                    return res
            except Exception as e:
                pass
        elif isinstance(ifd, datetime):
            return ifd
        return pd.NaT
