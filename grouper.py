from pathlib import Path
from datetime import datetime, timedelta
import numpy as np


def file_date_gen(base_path, glob='**\*.jpg', date_format='%Y-%m-%d_%H.%M.%S'):
    for file in Path(base_path).glob(glob):
        try:
            yield file, datetime.strptime(file.stem, date_format)
        except ValueError as e:
            UNCONVERTED_STR = 'unconverted data remains: '
            if UNCONVERTED_STR in str(e):
                uncoverted_portion = str(e).split(UNCONVERTED_STR)[1].strip()
                yield file, datetime.strptime(file.stem[:-len(uncoverted_portion)], date_format)


def files_and_dates(base_path, **kwargs):
    files, dates = zip(*[(file, date) for file, date in file_date_gen(base_path, **kwargs)])
    return list(files), list(dates)


def get_groups(base_path, time_threshold=3, **kwargs):
    if not isinstance(time_threshold, timedelta):
        time_threshold = timedelta(days=time_threshold)

    files, dates = files_and_dates(base_path, **kwargs)

    dates = np.array(dates)
    cuts = np.argwhere(np.diff(dates) > time_threshold).flatten() + 1

    file_groups = np.split(files, cuts)
    date_groups = np.split(dates, cuts)

    return zip(file_groups, date_groups)

def sort_group(base_path, group_threshold=5, **kwargs):
    fmt = '%Y-%m-%d'
    for files, dates in get_groups(base_path, **kwargs):
        if len(files) >= group_threshold:
            print(f'{dates[0].strftime(fmt)} to {dates[-1].strftime(fmt)}, {len(dates)} files')
