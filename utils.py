import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)

def get_unique_filename(path: Path) -> Path:
    if path.exists():
        files = [f for f in path.parents[0].glob(f'{path.stem}*')]
        res = path.with_name(f'{path.stem}({len(files)}){path.suffix}')
        LOGGER.debug(f'unique filepath: "{res}"')
        return res
    else:
        return path


def get_jpg_size(path):
    with open(path, 'rb') as file:
        file.seek(163)
        h = file.read(2)
        height = (h[0] << 8) + h[1]

        w = file.read(2)
        width = (w[0] << 8) + w[1]

        return width, height
