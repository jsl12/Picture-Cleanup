import shutil
from pathlib import Path

import log
import utils


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
        paths = [Path(m.group(1)) for m in log.PATH_REGEX.finditer(line)]
        if paths[1] == target:
            return paths[0]

def move_to_purgatory(logfile, purgatory_path):
    files = set([path for line, path in log.errors(logfile)])
    for f in files:
        shutil.copy2(f, purgatory_path / f.name)
