import logging

from utils import match_date_patterns

LOGGER = logging.getLogger(__name__)


def parse_date_from_path(path):
    for key, handler in HANDLERS.items():
        if key in str(path.resolve()):
            handler = globals()[handler] if isinstance(handler, str) else handler
            return handler(path)
    else:
        return match_date_patterns(path)


def parse_google_photo(path):
    file_date = match_date_patterns(path)
    if file_date is not None:
        try:
            year = int(path.parents[1].name)
        except:
            LOGGER.info(f'bad year: {path.parents[1].name}')
        else:
            if (1990 <= year <= 2050):
                file_date = file_date.replace(year=year)

        try:
            month = int(path.parents[0].name)
        except:
            LOGGER.info(f'bad month: {path.parents[0].name}')
        else:
            if (1 <= month <= 12):
                file_date = file_date.replace(month=month)
        return file_date
    else:
        LOGGER.info(f'unmatched filename: "{path.name}"')


HANDLERS = {
    'Google Photos': parse_google_photo
}
