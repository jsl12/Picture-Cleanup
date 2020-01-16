import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path


LOGGER = logging.getLogger(__name__)


def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        res = path.with_name(f'{path.stem}({len(files)}){path.suffix}')
        LOGGER.debug(f'unique filepath: "{res}"')
        return res
    else:
        return path


def remove_empty_dirs(base):
    to_remove = []
    for dir in base.glob('**\*'):
        if dir.is_dir():
            contents = [p for p in dir.iterdir()]
            if len(contents) == 0:
                to_remove.append(dir)
    for d in to_remove:
        d.rmdir()


def hash(input):
    m = hashlib.md5()
    if not isinstance(input, list):
        input = [input]
    for info in input:
        if isinstance(info, str):
            m.update(bytes(info, encoding='UTF-8', errors='strict'))
        else:
            m.update(bytes(info))
    return m.hexdigest()

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
    except Exception as e:
        pass

def dfs_to_file(df_list, file):
    with Path(file).open('w') as f:
        for df in df_list:
            f.write(('-' * 50) + '\n')
            for idx, row in df.iterrows():
                f.write('    '.join([
                    str(row["pathdate"].date()),
                    str(row["filename"]),
                    f'{row["st_size"] / 1000:.2f} kB',
                    str(row["path"])
                ]) + '\n')
