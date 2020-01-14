import re
from pathlib import Path
from datetime import datetime
import logging


LOGGER = logging.getLogger(__name__)


def file_gen(path, ext='jpg'):
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


def parse_date_from_path(path):
    for key, handler in HANDLERS.items():
        if key in str(path.resolve()):
            handler = globals()[handler] if isinstance(handler, str) else handler
            return handler(path)


PATTERNS = [
    (re.compile('((19|20)\d{6}_\d{6})'), '%Y%m%d_%H%M%S'),
    (re.compile('((19|20)\d{12})'), '%Y%m%d%H%M%S')
]


def parse_google_photo(path):
    try:
        year = int(path.parents[1].name)
    except:
        LOGGER.info(f'bad year: {path.parents[1].name}')
        year = None

    try:
        month = int(path.parents[0].name)
    except:
        LOGGER.info(f'bad month: {path.parents[0].name}')
        month = None

    for regex, date_fmt in PATTERNS:
        m = regex.search(str(path.name))
        if m is not None:
            date_str = m.group(1)
            try:
                file_date = datetime.strptime(date_str, date_fmt)
            except ValueError as e:
                LOGGER.error(f'bad date: {path.name} does not match {date_fmt}')
                continue

            if year is not None and (1990 <= year <= 2050):
                file_date = file_date.replace(year=year)
            if month is not None and (1 <= month <= 12):
                file_date = file_date.replace(month=month)

            return file_date

    else:
        LOGGER.info(f'unmatched filename: "{path.name}"')


HANDLERS = {
    'Google Photos': parse_google_photo
}
