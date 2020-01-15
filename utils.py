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


def paths_from_dir_txt(path, ext='jpg'):
    path = Path(path)
    for file in path.glob('*.txt'):
        with file.open('r') as f:
            line = True
            while line:
                line = f.readline()
                try:
                    p = Path(line.strip())
                except Exception as e:
                    continue
                else:
                    if ext is not None and p.suffix == f'.{ext}':
                        yield p
                    elif ext is None and p.suffix != '':
                        yield p


date_regex = re.compile('(?P<year>(19|20)\d{2})(?P<delim>[- _\\\\]?)(?P<month>(0[1-9]|1[0-2]))')
def scan_date(path):
    m = date_regex.search(str(path))
    if m is not None:
        return datetime(
            year=int(m.group('year')),
            month=int(m.group('month')),
            day=1
        )
