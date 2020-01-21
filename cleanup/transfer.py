import ftplib
import logging
from pathlib import Path
from . import log

LOGGER = logging.getLogger(__name__)


def pull_from_phone(
        host,
        port,
        local_path,
        phone_path=None,
        ext='jpg',
        user='android',
        passwd='android'):
    ftp = ftplib.FTP()
    ftp.connect(host, port)
    try:
        LOGGER.debug(f'Connected to {host}:{port}')

        ftp.login(user, passwd)
        LOGGER.debug(f'Logged in with: {user}, {passwd}')

        for file in ftp_files(ftp, phone_path):
            if file.suffix == f'.{ext}':
                res = local_path / file.name
                if res.exists():
                    LOGGER.info(f'file already exists: "{res}"')
                    continue
                else:
                    if not res.parents[0].exists():
                        res.parents[0].mkdir()
                        LOGGER.debug(f'Created dir: "{res.parents[0]}"')

                    with res.open('wb') as res_file:
                        ftp.retrbinary(f'RETR {file}', res_file.write)
                    LOGGER.info(f'ftp success: "{file}", "{res}"')
    except Exception as e:
        LOGGER.exception(repr(e))
    finally:
        ftp.quit()


def ftp_files(ftp, path):
    for f in ftp.mlsd(path, facts=['type']):
        if f[1]['type'] == 'dir':
            yield from ftp_files(ftp, f'{path}\\{f[0]}')
        else:
            yield Path(path) / f[0]


def transferred_files(ftplog):
    for line in log.filter(log.line_gen(ftplog), 'ftp success'):
        yield (log.get_paths(line))


def skipped_files(ftplog):
    for line in log.filter(log.line_gen(ftplog), 'file already exists'):
        yield (log.get_paths(line))
