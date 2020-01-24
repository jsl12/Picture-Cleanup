import logging
from pathlib import Path
import functools
import time
import pandas as pd

LOGGER = logging.getLogger(__name__)


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        print(f'Finished {func.__name__!r} in {time.perf_counter()-start:.2f}s')
        return res
    return wrapper

def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        res = path.with_name(f'{path.stem}({len(files)}){path.suffix}')
        LOGGER.debug(f'unique filepath: "{res}"')
        return res
    else:
        return path


def remove_empty_dirs(base):
    to_remove = []
    for folder in base.glob('**\*'):
        if folder.is_dir():
            contents = [p for p in folder.iterdir()]
            if len(contents) == 0:
                to_remove.append(folder)
    for d in to_remove:
        d.rmdir()


def dfs_to_file(df_list, file):
    with Path(file).open('w') as f:
        for df in df_list:
            f.write(('-' * 50) + '\n')
            for idx, row in df.iterrows():
                f.write('    '.join([
                    str(row["pathdate"].date()),
                    str(row["filename"]),
                    f'{row["st_size"] / 1000:.2f} kB',
                    str(row["path"])
                ]) + '\n')


def paths_from_dir_txt(path, ext='jpg'):
    path = Path(path)
    for file in path.glob('*.txt'):
        with file.open('r') as f:
            line = True
            while line:
                line = f.readline()
                try:
                    p = Path(line.strip())
                except Exception as e:
                    continue
                else:
                    if ext is not None and p.suffix == f'.{ext}':
                        yield p
                    elif ext is None and p.suffix != '':
                        yield p


def df_from_dir_texts(source):
    files = [f for f in check.paths_from_dir_txt(source)]
    return pd.DataFrame(
        data={
            'path': files,
            'filename': [f.name for f in files]
        }
    )


def duplicate_sets(df: pd.DataFrame, keys=None, min=1):
    yield from (
        dup_set                                         # dup_set is a DataFrame
        for idx, dup_set in                # with the groupby object, the iterations will also have the 2 values it is grouping by
        df.groupby(keys or ['filename', 'st_size'])     # group all the sets with unique combinations of values specified by keys
        if dup_set.shape[0] > min                       # only if the set contains more than 1 item
    )


def dupicates_to_file(df: pd.DataFrame, file, keys=None):
    return utils.dfs_to_file(duplicate_sets(df, keys), file)