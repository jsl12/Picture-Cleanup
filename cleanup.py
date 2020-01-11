import datetime
import shutil
from pathlib import Path
from typing import List

from exif import Image


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
        # Ensure the directory will exist
        if not dest.parents[0].exists():
            dest.parents[0].mkdir(parents=True)

        # Check for duplicates
        if dest.exists():
            source_exif = read_exif(source)
            dest_exif = read_exif(dest)

            ATTRIBUTES = [
                'image_unique_id',
                'make',
                'model',
                'image_height',
                'image_width'
            ]
            try:
                if all([getattr(source_exif, att) == getattr(dest_exif, att) for att in ATTRIBUTES]):
                    print(f'Skipping duplicate {dest.name}')
                    continue
            except AttributeError:
                pass

        # Ensure the filename will be unique
        dest = get_unique_filename(dest)

        # Copy file with as much metadata from the file system as possible, should preserve last modified time, etc.
        # https://docs.python.org/3/library/shutil.html#shutil.copy2
        print(f'Copying {source.name}')
        shutil.copy2(source, dest)

def gather_jpg(source_path: Path) -> List[Path]:
    return [f for f in source_path.glob('**\*.jpg')]

def gen_date_paths(files: List[Path], dest_parent: Path, filename_format:str = '%Y-%m-%d_%H.%M.%S.jpg') -> List[Path]:
    print(f'Reading exif data from {len(files)} files...')
    dates = [read_exif_date(f) for f in files]
    res = [dest_parent / d.strftime('%Y') / d.strftime('%B') / d.strftime(filename_format) for d in dates]
    return res

def read_exif_date(path: Path) -> datetime.datetime:
    exif_data = read_exif(path)
    if hasattr(exif_data, 'datetime_original'):
        date_str = exif_data.datetime_original
    elif hasattr(exif_data, 'datetime'):
        date_str = exif_data.datetime
    return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

def read_exif(path: Path) -> Image:
    print(f'Reading exif data from {path.name}')
    with path.open('rb') as file:
        return Image(file)

def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        return path.with_name(f'{path.stem}({len(files)}){path.suffix}')
    else:
        return path
