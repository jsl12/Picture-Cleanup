import PIL
import exif
from pathlib import Path
import os
import logging
from datetime import datetime

LOGGER = logging.getLogger(__name__)
OS_ATTRIBUTES = ['st_mtime', 'st_mtime_ns', 'st_size']
EXIF_ATTRIBUTES = [
                # 'image_unique_id',
                'make',
                'model',
                'image_height',
                'image_width'
            ]


class MetaDataException(Exception):
    pass


class ExifReadFail(MetaDataException):
    def __init__(self, path):
        LOGGER.error(f'failed to read exif data from: "{path}"')


class MissingDateField(MetaDataException):
    def __init__(self, metadata_dict):
        LOGGER.error(f'No date field in: {list(metadata_dict.keys())}')


class DateParseFail(MetaDataException):
    def __init__(self, date_str, format):
        LOGGER.error(f'Failed to parse "{date_str}" with "{format}"')


class MissingComparisonField(MetaDataException):
    def __init__(self, missing_field):
        LOGGER.error(f'Missing comparison field: {missing_field}')


def read_os_metadata(path):
    path = Path(path)
    LOGGER.info(f'read os stat: "{path.resolve()}"')
    res = os.stat(path)
    return {key: getattr(res, key) for key in dir(res) if 'st_' in key}


def read_exif_metadata(path):
    path = Path(path).resolve()
    LOGGER.info(f'read exif start: "{path}"')
    with path.open('rb') as file:
        try:
            img = exif.Image(file)
        except:
            LOGGER.error(f'read exif fail: "{path}"')
            raise ExifReadFail(path)
        else:
            LOGGER.info(f'read exif end: "{path}"')
            if img.has_exif:
                res = {}
                failed = []
                for k in dir(img):
                    try:
                        res[k] = getattr(img, k)
                    except:
                        failed.append(k)
                        continue
                if len(failed) > 0:
                    LOGGER.debug(f'Failed to read from exif: {", ".join(failed)}')
                return res
            else:
                LOGGER.info(f'read exif: empty data "{path}"')


def determine_date(metadata_dict, format:str = '%Y:%m:%d %H:%M:%S') -> datetime:
    if 'datetime_original' in metadata_dict:
        date_str = metadata_dict['datetime_original']
    elif 'datetime' in metadata_dict:
        date_str = metadata_dict['datetime']
    elif 'st_mtime' in metadata_dict:
        try:
            return datetime.fromtimestamp(metadata_dict['st_mtime'])
        except:
            raise DateParseFail(metadata_dict['st_mtime'], f'datetime.fromtimestamp()')
    else:
        raise MissingDateField(metadata_dict)

    try:
        return datetime.strptime(date_str, format)
    except:
        raise DateParseFail(date_str, format)


def check_duplicates(meta1, meta2, type=None, keywords=None):
    if type is None:
        assert keywords is not None
        to_check = keywords
    elif type == 'os':
        to_check = OS_ATTRIBUTES
    elif type == 'exif':
        to_check = EXIF_ATTRIBUTES

    # add any additional keywords
    if isinstance(keywords, list):
        to_check.extend(keywords)

    # always check the size if available
    if 'st_size' in meta1 and 'st_size' in meta2:
        to_check.append('st_size')

    for att in to_check:
        try:
            if meta1[att] != meta2[att]:
                LOGGER.info(f'not duplicates: {att}: {meta1[att]} != {meta2[att]}')
                return False
        except KeyError:
            raise MissingComparisonField(att)
    else:
        LOGGER.info(f'duplicates based on: {", ".join(to_check)}')
        return True


def check_duplicates_os(stats1, stats2, keywords=None):
    to_check = keywords or OS_ATTRIBUTES
    return all([stats1[att] == stats2[att] for att in to_check])


def check_duplicates_exif(exif_data1, exif_data2, keywords=None):
    to_check = keywords or EXIF_ATTRIBUTES
    return all([exif_data1[att] == exif_data2[att] for att in to_check])
