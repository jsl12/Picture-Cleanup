import logging
import re
import sys
from pathlib import Path


PATH_REGEX = re.compile('"(.+?)"')


def configure(file=None, append=False, stream_level=logging.WARNING, file_level=logging.DEBUG):
    log_stream = logging.StreamHandler(sys.stdout)
    log_stream.setLevel(stream_level)
    handlers = [log_stream]

    if file is not None:
        file_logger = logging.FileHandler(file, 'a' if append else 'w')
        file_logger.setLevel(file_level)
        handlers.append(file_logger)

    logging.basicConfig(level=logging.DEBUG, handlers=handlers)


def copied_files(logfile):
    for line in filter(line_gen(logfile), 'end copy'):
        yield tuple(get_paths(line))


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
