from typing import List

import pandas as pd


def filter_extension(df, include_list, path_col='path'):
    return pd.DataFrame(data={e: df[path_col].apply(lambda p: p.suffix.upper()) == e.upper() for e in include_list}).any(axis=1)


def filter_path(df: pd.DataFrame, filter_list: List[str], path_col: str = 'path', case: bool = False) -> pd.Series:
    return pd.DataFrame(data={folder: df[path_col].apply(str).str.contains(folder, case=case) for folder in filter_list}).any(axis=1)
