from dataclasses import dataclass
from typing import List

import pandas as pd

from .processor import Processor
from ..df.utils import scan_pathdate


@dataclass
class ScanPathDate(Processor):
    source_col:str = 'path'
    res_col: str = 'pathdate'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.res_col] = scan_pathdate(df, self.source_col)
        return df


@dataclass
class DateSelector(Processor):
    source_cols: List[str]
    res_col:str = 'selected_date'
    null_col: str = 'valid date'

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.res_col] = df.apply(self.select_from_row, cols=self.source_cols, axis=1)
        df[self.null_col] = ~pd.isnull(df['selected_date'])
        return df

    @staticmethod
    def select_from_row(row: pd.Series, cols: List[str]):
        for c in cols:
            if c in row:
                if not pd.isnull(row[c]):
                    return row[c]
        else:
            return pd.NaT