import datetime
import re
import shutil
from pathlib import Path
from typing import List

import numpy as np
from exif import Image


def copy_and_rename(source_path, destination_path, filename_format:str = '%Y-%m-%d_%H.%M.%S.jpg'):
    source_path = Path(source_path)
    destination_path = Path(destination_path)
    if not destination_path.exists():
        destination_path.mkdir(parents=True)

    files = source_path.glob('**\*.jpg')
    for original_file in files:
        print('-' * 25)
        print(original_file.relative_to(source_path))

        # read the exif data
        with open(original_file, 'rb') as file:
            exif_data = Image(file)

        # get the date from the exif data
        try:
            pic_date = datetime.datetime.strptime(exif_data.datetime_original, '%Y:%m:%d %H:%M:%S')
        except AttributeError as e:
            # sometimes there's only a 'datetime' attribute
            pic_date = datetime.datetime.strptime(exif_data.datetime, '%Y:%m:%d %H:%M:%S')

        # generate path for new file
        newfile = get_unique_filename(destination_path / pic_date.strftime(filename_format))

        # make sure we're not overwriting anything
        if newfile.exists():
            print(f'File already exists: {newfile.name}')
        else:
            print(newfile.name)
            with newfile.open('wb') as file:
                file.write(exif_data.get_file())


def get_unique_filename(path: Path):
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        return path.with_name(f'{path.stem}({len(files)}){path.suffix}')
    else:
        return path


def sort_folder(path):
    date_format = '%Y-%m-%d'
    file_groups = group_dates(path)
    for group in file_groups:
        start = datetime_from_filename(group[0])
        end = datetime_from_filename(group[-1])
        group_folder = path / f'{start.strftime(date_format)} to {end.strftime(date_format)}'
        group_folder.mkdir(parents=True)
        for file in group:
            shutil.move(str(file), str(group_folder / file.name))


def group_dates(path, num_days=3, glob='*.jpg'):
    files = [f for f in path.glob(glob)]
    dates = [datetime_from_filename(f) for f in files]
    cuts = np.argwhere(np.diff(dates) > datetime.timedelta(days=num_days)).flatten() + 1
    groups = np.split(files, cuts)
    return groups


DATE_REGEX = re.compile('^\d+-\d+-\d+_\d+\.\d+\.\d+')
def datetime_from_filename(path, regex=None):
    regex = regex or DATE_REGEX
    date_str = regex.match(path.stem).group()
    return datetime.strptime(date_str, '%Y-%m-%d_%H.%M.%S')

def copy_and_sort(
        source_path,
        dest_path,
        collect_func = None,
        sort_func = None):

    source_path = Path(source_path)
    assert source_path.exists()

    dest_path = Path(dest_path)
    if not dest_path.exists():
        dest_path.mkdir(parents=True)

    # gather all files into a single list
    collect_func = collect_func or gather_jpg
    files = collect_func(source_path)

    # generate destination paths
    # sort_func is a Tuple (function_pointer, arg1, arg2, arg3...)
    sort_func = sort_func or (gen_date_paths, dest_path)
    # calls the function pointer with the list of file Paths as the first argument and the rest of the Tuple as further positional arguments
    res_paths = sort_func[0](files, *sort_func[1:])

    for source, dest in zip(files, res_paths):
        # https://docs.python.org/3/library/shutil.html#shutil.copy2
        shutil.copy2(source, dest)

def gather_jpg(source_path: Path) -> List[Path]:
    return [f for f in source_path.glob('**\*.jpg')]

def gen_date_paths(files: List[Path], dest_parent: Path, filename_format:str = '%Y-%m-%d_%H.%M.%S.jpg') -> List[Path]:
    print(f'Reading exif data from {len(files)} files...')
    dates = [read_exif_date(f) for f in files]
    res = [dest_parent / d.strftime('%Y') / d.strftime('%B') / d.strftime(filename_format) for i, d in enumerate(dates)]
    return res

def read_exif_date(path: Path) -> datetime.datetime:
    with path.open('rb') as file:
        exif_data = Image(file)

    if hasattr(exif_data, 'datetime_original'):
        date_str = exif_data.datetime_original
    elif hasattr(exif_data, 'datetime'):
        date_str = exif_data.datetime

    return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')