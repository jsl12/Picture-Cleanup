import logging
from datetime import datetime
from pathlib import Path

from utils import match_date_patterns

LOGGER = logging.getLogger(__name__)


def parse_date_from_path(path):
    path = Path(path)
    for key, handler in HANDLERS.items():
        if key in str(path.resolve()):
            handler = globals()[handler] if isinstance(handler, str) else handler
            return handler(path)
    else:
        return match_date_patterns(path)


def parse_google_photo(path):
    log_prefix = 'google photo: '
    file_date = match_date_patterns(path)
    if file_date is not None:
        try:
            year = int(path.parents[1].name)
        except:
            LOGGER.info(f'{log_prefix}bad year: {path.parents[1].name}')
        else:
            if (1990 <= year <= 2050):
                file_date = file_date.replace(year=year)

        try:
            month = int(path.parents[0].name)
        except:
            LOGGER.info(f'{log_prefix}bad month: {path.parents[0].name}')
        else:
            if (1 <= month <= 12):
                file_date = file_date.replace(month=month)

        LOGGER.debug(f'{log_prefix}parsed date:{file_date.strftime("%Y-%m-%d")}, {path.name}')
        return file_date
    else:
        LOGGER.info(f'{log_prefix}unmatched filename:"{path.name}"')


def parse_lightroom(path):
    log_prefix = 'lightroom: '
    fmt = '%Y-%m-%d'
    try:
        file_date = datetime.strptime(path.parents[0].name, fmt)
    except Exception as e:
        file_date = match_date_patterns(path)
    else:
        LOGGER.debug(f'{log_prefix}parsed date: {file_date.strftime(fmt)}, {path.name}')
    finally:
        if file_date is None:
            LOGGER.info(f'{log_prefix}unmatched filename:"{path.name}"')
        return file_date


HANDLERS = {
    'Google Photos': parse_google_photo,
    'Lightroom CC': parse_lightroom
}
