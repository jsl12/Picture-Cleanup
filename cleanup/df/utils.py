import logging
import re
from datetime import datetime
from pathlib import Path

import exifread
import pandas as pd
import yaml

from ..utils import timer

LOGGER = logging.getLogger(__name__)

@timer
def load_yaml(yaml_path):
    with Path(yaml_path).open('r') as file:
        cfg = yaml.load(file, Loader=yaml.SafeLoader)
    df_path = Path(cfg['df'])
    print(f'Loading {df_path.stat().st_size / (10 ** 6):.2f} MB...')
    df = pd.read_pickle(df_path)
    print(f'Loaded {df.shape[0]} rows')


def read_os_stats(path: Path):
    LOGGER.debug(f'getting os stats: "{path}"')
    stat_obj = Path(path).stat()
    return {key: getattr(stat_obj, key) for key in dir(stat_obj) if key[:3] == 'st_'}


def read_exif(path: Path, stop_tag=exifread.DEFAULT_STOP_TAG):
    LOGGER.debug(f'getting exif data: "{path}"')
    try:
        with Path(path).open('rb') as f:
            return exifread.process_file(f, details=False, stop_tag=stop_tag)
    except PermissionError as e:
        return {}


def scan_pathdate(df, scan_col='path'):
    return df[scan_col].apply(lambda p: scan_date(p) or pd.NaT)


date_regex = re.compile(
    '(?P<year>(19|20)\d{2})'    # year
    '[- _\\\\]?'                # delimter between year and month, could be \ between paths
    '(?P<month>[01]\d{1})'      # month
    '([- _]?'                   # delimter between month and day
    '(?P<day>\d{2}))?'          # day (optional)
)


def scan_date(path):
    m = date_regex.search(str(path))
    try:
        if m is not None:
            res = m.groupdict()
            year = int(res['year'])
            month = int(res['month'])
            day = int(res['day'] or 1)
            if day == 0:
                day += 1
            if ((1950 <= year <= 2050) and
                (1 <= month <= 12) and
                    (1 <= day <= 31)):
                return datetime(
                    year=year,
                    month=month,
                    day=day
                )
    except Exception:
        pass
    return pd.NaT
