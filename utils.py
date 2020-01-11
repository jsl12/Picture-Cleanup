from exif import Image
from datetime import datetime
from pathlib import Path

class ExifException(Exception):
    pass


def read_exif(path, quiet=True) -> Image:
    if not quiet:
        print(f'Reading exif data from {path.name}')
    with path.open('rb') as file:
        try:
            return Image(file)
        except:
            raise ExifException(f'{path.name}')


def extract_date_from_exif(exif_data: Image) -> datetime:
    if hasattr(exif_data, 'datetime_original'):
        date_str = exif_data.datetime_original
    elif hasattr(exif_data, 'datetime'):
        date_str = exif_data.datetime
    else:
        raise AttributeError(f'Could not determine date from exif data')
    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')


def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        return path.with_name(f'{path.stem}({len(files)}){path.suffix}')
    else:
        return path
