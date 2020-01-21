import logging
import shutil
from datetime import timedelta
from pathlib import Path

import numpy as np

from . import utils
from .df import scan_date

LOGGER = logging.getLogger(__name__)


def files_and_dates(base_path, **kwargs):
    files, dates = zip(*[(file, date) for file, date in file_date_gen(base_path, **kwargs)])
    return list(files), list(dates)


def file_date_gen(base_path, glob='**\*.jpg'):
    for file in Path(base_path).glob(glob):
        try:
            yield file, scan_date(file)
        except Exception as e:
            pass


def get_groups(base_path, time_threshold=3, **kwargs):
    if not isinstance(time_threshold, timedelta):
        time_threshold = timedelta(days=time_threshold)

    files, dates = files_and_dates(base_path, **kwargs)

    dates = np.array(dates)
    cuts = np.argwhere(np.diff(dates) > time_threshold).flatten() + 1

    file_groups = np.split(files, cuts)
    date_groups = np.split(dates, cuts)

    yield from zip(file_groups, date_groups)

def sort_group(base_path, group_min_size=5, suffix=' (desc)', **kwargs):
    fmt = '%m-%d'
    for files, dates in get_groups(base_path, **kwargs):
        if len(files) >= group_min_size:
            start = dates[0].strftime(fmt)
            end = dates[-1].strftime(fmt)
            if start == end:
                folder_name = f'{start}{suffix}'
            else:
                folder_name =  f'{start} to {end}{suffix}'
            res_parent = base_path / dates[0].strftime('%Y') / folder_name
            LOGGER.info(f'group: {folder_name}, {len(files)} files')
        else:
            res_parent = base_path / dates[0].strftime('%Y') / dates[0].strftime('%m - %B')

        if not res_parent.exists():
            res_parent.mkdir(parents=True)

        for file in files:
            res = res_parent / file.name
            if file != res:
                LOGGER.info(f'move start: "{file}", "{res}"')
                try:
                    shutil.move(file, res)
                except:
                    LOGGER.error(f'move fail "{file}", "{res}"')
                    continue
                else:
                    LOGGER.info(f'move end: "{file}", "{res}"')
    utils.remove_empty_dirs(base_path)
