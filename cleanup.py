import shutil
from pathlib import Path

import utils

ATTRIBUTES = [
                # 'image_unique_id',
                'make',
                'model',
                'image_height',
                'image_width'
            ]


def copy_and_sort(source, dest_parent, ext='jpg', recursive=True, **kwargs):
    glob_pattern = f'**\*.{ext}' if recursive else f'*.{ext}'
    file_generator = Path(source).glob(glob_pattern)
    sorted_files = sort_gen(file_generator, dest_parent, **kwargs)
    for original, dest in sorted_files:
        # create parent directory for new file if it doesn't exist
        if not dest.parents[0].exists():
            dest.parents[0].mkdir(parents=True)

        # double-check that we're not about to overwrite anything
        if not dest.exists():
            print(f'Copying {dest.relative_to(dest_parent)}')
            shutil.copy2(original, dest)


def sort_gen(source_gen, dest_parent, filename_format:str = '%Y-%m-%d_%H.%M.%S.jpg', exclude_folders=None):
    for file in source_gen:
        if ((exclude_folders is not None) and
                (any([exc in str(file.parents[0]) for exc in exclude_folders]))):
            continue

        print('-' * 50)
        try:
            exif_orig = utils.read_exif(file, quiet=False)
            pic_date = utils.extract_date_from_exif(exif_orig)
            res_path = dest_parent / pic_date.strftime('%Y') / pic_date.strftime('%B') / pic_date.strftime(filename_format)

            if res_path.exists():
                print(f'{res_path.name} already exists, checking for duplicates')
                dest_exif = utils.read_exif(res_path, quiet=False)
                try:
                    if check_duplicates(exif_orig, dest_exif):
                        print(f'{file.name} is duplicate of {res_path.name}')
                        continue
                except AttributeError:
                    with open('missing.txt', 'a') as file:
                        file.write(f'{file}, {res_path.relative_to(dest_parent)}\n')
                    pass

            res_path = utils.get_unique_filename(res_path)
            print(f'New file: {res_path.relative_to(dest_parent)}')
            yield file, res_path

        except utils.ExifException as e:
            print(f'Problem reading exif data from {e}, skipping file')
            continue


def check_duplicates(exif_data1, exif_data2):
    # if both sets of data have the image_unique_id field, that's pretty easy to use
    unique_tag = 'image_unique_id'
    if hasattr(exif_data1, unique_tag) and hasattr(exif_data2, unique_tag):
        return getattr(exif_data1, unique_tag) == getattr(exif_data2, unique_tag)
    # otherwise try to match all the attributes in ATTRIBUTES
    else:
        return all([getattr(exif_data1, att) == getattr(exif_data2, att) for att in ATTRIBUTES])
