import logging
from datetime import datetime
from pathlib import Path

from utils import match_date_patterns, process_date_pattern, PATTERNS

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
    def style(parts):
        return datetime(
            year=int(parts[0]),
            month=int(parts[1]),
            day=1
        )

    def style2(parts):
        return datetime(
            year=int(parts[-3]),
            month=int(parts[-2]),
            day=1
        )

    def style3(parts):
        return match_date_patterns(parts[-1])

    log_prefix = 'google photo: '
    for path_style in [style, style2, style3]:
        try:
            parts = str(path).split('Google Photos\\')[1].split('\\')
            file_date = path_style(parts)
        except (ValueError, IndexError) as e:
            continue
        except Exception as e:
            LOGGER.exception(repr(e))
        else:
            if file_date is not None:
                LOGGER.debug(f'{log_prefix}path style: {path_style}')
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
        file_date = match_date_patterns(path.name)
    else:
        LOGGER.debug(f'{log_prefix}parsed date: {file_date.strftime(fmt)}, {path.name}')
    finally:
        if file_date is None:
            LOGGER.info(f'{log_prefix}unmatched filename:"{path.name}"')
        return file_date


def parse_picasa(path):
    log_prefix = 'picasa: '
    fmt = '%Y-%m-%d'
    try:
        input = str(path).split('Picasa')[1]
        file_date = process_date_pattern(input, *PATTERNS[2])
    except Exception as e:
        file_date = None
    else:
        LOGGER.debug(f'{log_prefix}parsed date: {file_date.strftime(fmt)}, {path.name}')
    finally:
        if file_date is None:
            LOGGER.info(f'{log_prefix}unmatched filename:"{path.name}"')
        return file_date


HANDLERS = {
    'Google Photos': parse_google_photo,
    'Lightroom CC': parse_lightroom,
    'Picasa': parse_picasa
}
