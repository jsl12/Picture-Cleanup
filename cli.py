import click
import yaml
import logging
from cleanup import copy_and_sort
import sys

@click.command()
@click.option('-cfg', '--config-path', 'yaml_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def copy_and_sort_yaml(yaml_path):
    with open(yaml_path, 'r') as file:
        cfg = yaml.load(file, yaml.SafeLoader)

    log_stream = logging.StreamHandler(sys.stdout)
    log_stream.setLevel(logging.WARNING)
    handlers=[log_stream]

    if cfg.get('log', None) is not None:
        file_logger = logging.FileHandler(cfg.pop('log'), 'w')
        file_logger.setLevel(logging.DEBUG)
        handlers.append(file_logger)

    logging.basicConfig(level=logging.DEBUG, handlers=handlers)

    return copy_and_sort(**cfg)


if __name__ == '__main__':
    copy_and_sort_yaml()