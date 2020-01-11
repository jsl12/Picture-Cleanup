import re
from datetime import datetime, timedelta
from pathlib import Path
from shutil import move

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
            pic_date = datetime.strptime(exif_data.datetime_original, '%Y:%m:%d %H:%M:%S')
        except AttributeError as e:
            # sometimes there's only a 'datetime' attribute
            pic_date = datetime.strptime(exif_data.datetime, '%Y:%m:%d %H:%M:%S')

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
            move(str(file), str(group_folder / file.name))


def group_dates(path, num_days=3, glob='*.jpg'):
    files = [f for f in path.glob(glob)]
    dates = [datetime_from_filename(f) for f in files]
    cuts = np.argwhere(np.diff(dates) > timedelta(days=num_days)).flatten() + 1
    groups = np.split(files, cuts)
    return groups


DATE_REGEX = re.compile('^\d+-\d+-\d+_\d+\.\d+\.\d+')
def datetime_from_filename(path):
    date_str = DATE_REGEX.match(path.stem).group()
    return datetime.strptime(date_str, '%Y-%m-%d_%H.%M.%S')


if __name__ == '__main__':
    source_folders = [
        r'M:\ARCHIVE\Pictures\2013',
        r'M:\ARCHIVE\Pictures\2014',
        r'M:\ARCHIVE\Pictures\Camping'
    ]
    dest_folder = Path(r'M:\ARCHIVE\Pictures\_cleaned')
    for folder in source_folders:
        copy_and_rename(
            source_path=folder,
            destination_path=dest_folder
        )
        sort_folder(dest_folder)