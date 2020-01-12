from exif import Image
from datetime import datetime
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)

class ExifException(Exception):
    pass

def read_exif(path) -> Image:
    LOGGER.info(f'read_exif: "{path}"')
    with path.open('rb') as file:
        try:
            return Image(file)
        except:
            LOGGER.error(f'read_exif fail: {path}')
            raise ExifException(f'{path.name}')


def extract_date_from_exif(exif_data: Image) -> datetime:
    try:
        if hasattr(exif_data, 'datetime_original'):
            date_str = exif_data.datetime_original
        elif hasattr(exif_data, 'datetime'):
            date_str = exif_data.datetime
        else:
            raise AttributeError(f'Could not determine date from exif data')
        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except:
        LOGGER.error(f'exif date fail: {exif_data}')
        raise ExifException(exif_data)


def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        res = path.with_name(f'{path.stem}({len(files)}){path.suffix}')
        LOGGER.debug(f'unique filepath: "{res}"')
        return res
    else:
        return path
