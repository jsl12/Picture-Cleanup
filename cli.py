import click
import yaml

from cleanup import copy_and_sort


@click.command()
@click.option('-cfg', '--config-path', 'yaml_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def copy_and_sort_yaml(yaml_path):
    with open(yaml_path, 'r') as file:
        cfg = yaml.load(file, yaml.SafeLoader)
    return copy_and_sort(**cfg)


if __name__ == '__main__':
    copy_and_sort_yaml()