import log
from pathlib import Path
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
