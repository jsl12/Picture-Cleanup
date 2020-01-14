import logging
import shutil
from pathlib import Path
from types import GeneratorType

import metadata
import utils

LOGGER = logging.getLogger(__name__)


def copy_and_sort(source, dest_parent, ext='jpg', recursive=True, test=False, **kwargs):
    if isinstance(source, GeneratorType):
        file_generator = source
    else:
        glob_pattern = f'**\*.{ext}' if recursive else f'*.{ext}'
        file_generator = Path(source).glob(glob_pattern)

    sorted_files = sort_gen(file_generator, dest_parent, **kwargs)
    for original, dest in sorted_files:
        try:
            # create parent directory for new file if it doesn't exist
            if not dest.parents[0].exists():
                if not test:
                    dest.parents[0].mkdir(parents=True)
                LOGGER.debug(f'mkdir: "{dest.parents[0]}"')

            # double-check that we're not about to overwrite anything
            if not dest.exists():
                LOGGER.info(f'start copy: "{original}", "{dest}"')
                if not test:
                    shutil.copy2(original, dest)
                LOGGER.warning(f'end copy: "{original}", "{dest}"')
        except Exception as e:
            LOGGER.exception(repr(e))


def sort_gen(source_gen, dest_parent, filename_format:str = '%Y-%m-%d_%H.%M.%S.jpg', exclude_folders=None):
    for file in source_gen:
        file = file.resolve()
        if ((exclude_folders is not None) and
                (any([exc in str(file.parents[0]) for exc in exclude_folders]))):
            LOGGER.debug(f'excluding: "{file}"')
            continue

        try:
            metadata_original = {}
            # read the exif metadata for the original file, keep going if it fails somehow
            try:
                metadata_original.update(metadata.read_exif_metadata(file))
            except:
                pass

            # read the os metadata for the original file
            metadata_original.update(metadata.read_os_metadata(file))

            # generate the result path from whatever is in the metadata
            pic_date = metadata.determine_date(metadata_original)
            res_path = Path(dest_parent) / pic_date.strftime('%Y') / pic_date.strftime('%m - %B') / pic_date.strftime(filename_format)

            # check to see if the result already exists
            if res_path.exists():
                # if they do, check the metadata of the files
                metadata_target = {}
                LOGGER.debug(f'pre-existing file: "{file}", "{res_path.relative_to(dest_parent)}"')

                # read os level metadata for the target
                metadata_target.update(metadata.read_os_metadata(res_path))

                # check if the files are duplicates at the OS level
                if metadata.check_duplicates(metadata_target, metadata_original, type='os'):
                    # if they are, then skip
                    LOGGER.warning(f'duplicates os: "{file}", "{res_path.relative_to(dest_parent)}"')
                    continue
                else:
                    # if not, read the exif metadata for the target
                    try:
                        metadata_target.update(metadata.read_exif_metadata(res_path))
                    except:
                        # if reading the exif data from the target file fails, then consider not duplicates
                        pass

                    # if everything goes OK, check for duplicates again, with type 'exif'
                    else:
                        try:
                            if metadata.check_duplicates(metadata_target, metadata_original, type='exif'):
                                # if the metadata indicates duplicates, log and skip
                                LOGGER.warning(f'duplicates exif: "{file}", "{res_path.relative_to(dest_parent)}"')
                                continue
                        except metadata.MissingComparisonField as e:
                            # if a field is missing, consider not a duplicate
                            pass

            # ensure there will be a unique filename
            res_path = utils.get_unique_filename(res_path)
            LOGGER.info(f'new file: "{file}", "{res_path.relative_to(dest_parent)}"')
            yield file, res_path

        # If it hits a predictable exception, then just skip and continue
        # MetaDataExceptions should all log themselves at the module level
        except metadata.MetaDataException as e:
            continue
        # If it hits something unexpected, fully log it and continue
        except Exception as e:
            LOGGER.exception(repr(e))
            continue
