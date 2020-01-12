import logging
import shutil
import sys
from pathlib import Path

import utils

ATTRIBUTES = [
                # 'image_unique_id',
                'make',
                'model',
                'image_height',
                'image_width'
            ]


LOGGER = logging.getLogger(__name__)
print_stream = logging.StreamHandler(sys.stdout)
print_stream.setLevel(logging.INFO)
log_file = logging.FileHandler('pic_cleanup.log', 'w')
log_file.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        print_stream,
        log_file
    ]
)


def copy_and_sort(source, dest_parent, ext='jpg', recursive=True, **kwargs):
    glob_pattern = f'**\*.{ext}' if recursive else f'*.{ext}'
    file_generator = Path(source).glob(glob_pattern)
    sorted_files = sort_gen(file_generator, dest_parent, **kwargs)
    for original, dest in sorted_files:
        try:
            # create parent directory for new file if it doesn't exist
            if not dest.parents[0].exists():
                dest.parents[0].mkdir(parents=True)
                LOGGER.debug(f'mkdir: {dest.parents[0]}')

            # double-check that we're not about to overwrite anything
            if not dest.exists():
                LOGGER.info(f'start copy: {original}, {dest}')
                shutil.copy2(original, dest)
                LOGGER.info(f'end copy: {original}, {dest}')
        except Exception as e:
            LOGGER.exception(repr(e))


def sort_gen(source_gen, dest_parent, filename_format:str = '%Y-%m-%d_%H.%M.%S.jpg', exclude_folders=None):
    for file in source_gen:
        if ((exclude_folders is not None) and
                (any([exc in str(file.parents[0]) for exc in exclude_folders]))):
            continue

        try:
            exif_orig = utils.read_exif(file)
            pic_date = utils.extract_date_from_exif(exif_orig)
            res_path = dest_parent / pic_date.strftime('%Y') / pic_date.strftime('%B') / pic_date.strftime(filename_format)

            if res_path.exists():
                LOGGER.debug(f'pre-existing file: {file}, {res_path.relative_to(dest_parent)}')
                dest_exif = utils.read_exif(res_path)
                try:
                    if check_duplicates(exif_orig, dest_exif):
                        LOGGER.info(f'duplicates: {file}, {res_path.relative_to(dest_parent)}')
                        continue
                except AttributeError:
                    for att in ATTRIBUTES:
                        if not hasattr(exif_orig, att):
                            LOGGER.warning(f'missing exif field: {att}, {file}')
                        if not hasattr(dest_exif, att):
                            LOGGER.warning(f'missing exif field: {att}, {res_path}')
                    pass

            res_path = utils.get_unique_filename(res_path)
            LOGGER.info(f'new file: {file}, {res_path.relative_to(dest_parent)}')
            yield file, res_path

        except utils.ExifException as e:
            continue


def check_duplicates(exif_data1, exif_data2):
    # if both sets of data have the image_unique_id field, that's pretty easy to use
    unique_tag = 'image_unique_id'
    if hasattr(exif_data1, unique_tag) and hasattr(exif_data2, unique_tag):
        return getattr(exif_data1, unique_tag) == getattr(exif_data2, unique_tag)
    # otherwise try to match all the attributes in ATTRIBUTES
    else:
        return all([getattr(exif_data1, att) == getattr(exif_data2, att) for att in ATTRIBUTES])
