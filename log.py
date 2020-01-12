from pathlib import Path


def filter(line_gen, filter_str):
    for line in line_gen:
        if filter_str in line:
            yield line


def line_gen(logfile):
    with Path(logfile).open('r') as file:
        line = True
        while line:
            line = file.readline()
            yield line.strip()
