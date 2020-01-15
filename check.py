import logging
import shutil
from pathlib import Path

import log
import pic_collections as pc
import utils
import time

LOGGER = logging.getLogger(__name__)

def check_exif(logfile):
    for line, path in log.errors(logfile):
        try:
            exif_data = utils.read_exif(path)
            pic_date = utils.extract_date_from_exif(exif_data)
        except:
            print(f'Bad exif data:\n{path}')
        else:
            print(f'Good exif data:\n{path}\n{pic_date.strftime("%y-%m-%d %H:%M:%S")}')


def find_source(logfile, target):
    for line in log.filter(log.line_gen(logfile), 'end copy'):
        paths = log.get_paths(line)
        if paths[1] == target:
            return paths[0]


def move_to_purgatory(logfile, purgatory_path):
    purgatory_path = Path(purgatory_path)
    if not purgatory_path.exists():
        purgatory_path.mkdir(parents=True)

    files = set([path for line, path in log.errors(logfile)])
    for f in files:
        shutil.copy2(f, Path(purgatory_path) / f.name)


def check_date_parse(source, logfile=None, glob_str=None):
    if logfile is not None:
        log.configure(logfile, stream_level=logging.INFO)

    if isinstance(glob_str, str):
        source = source.glob(glob_str)
    else:
        source = utils.paths_from_dir_txt(source)

    start = time.time()
    total, parsed = 0, 0
    for path in source:
        total += 1
        try:
            pathdate = pc.parse_date_from_path(path)
        except Exception as e:
            LOGGER.exception(repr(e))
            continue
        else:
            if pathdate is not None:
                parsed += 1
                LOGGER.info(f'parsed date: "{path}"')
            else:
                LOGGER.info(f'date parse fail: "{path}"')
    end = time.time()
    parse_time = end - start
    parse_rate = (parsed / total) * 100
    LOGGER.info(f'parse time: {parse_time :.2f}s')
    LOGGER.info(f'parse rate: {parse_rate :.2f}s')
    return parse_rate, parse_time

def parse_rate(logfile):
    parsed = 0
    failed = 0
    total = 0
    for line in log.line_gen(logfile):
        total += 1
        if 'parse' in line:
            parsed += 1
        elif 'fail' in line:
            failed += 1
    return (parsed / total)
