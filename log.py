import re
from pathlib import Path

PATH_REGEX = re.compile('"(.+?)"')


def copied_files(logfile):
    for line in filter(line_gen(logfile), 'end copy'):
        yield tuple([Path(path_str.group(1)) for path_str in PATH_REGEX.finditer(line)])


def errors(logfile):
    for line in line_gen(logfile):
        if 'INFO' in line and 'read' in line:
            last_read = line
        elif 'ERROR' in line:
            yield line, get_paths(last_read)[0]


def filter(line_gen, filter_str):
    if isinstance(filter_str, str):
        filter_str = [filter_str]

    if isinstance(filter_str, list) and all([isinstance(s, str) for s in filter_str]):
        for line in line_gen:
            if all([s in line for s in filter_str]):
                yield line
    else:
        raise ValueError(f'Invalid filter: {filter_str}')


def line_gen(logfile):
    with Path(logfile).open('r') as file:
        line = True
        while line:
            line = file.readline()
            yield line.strip()


def get_paths(line):
    return [Path(m.group(1)) for m in PATH_REGEX.finditer(line)]
