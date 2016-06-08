#!/usr/bin/env python3
"""Short script to create a new tarsnap backup"""
import datetime
import logging
import os
import re
import shlex
import subprocess
import time

import list_filters

AGING_PARAMS = [(0.5/24, 2),
                (1, 14),
                (7, 60),
                (30, 730),
                (365, -1)]
DATE_FORMAT = '%Y-%m-%d_%Hh%Mm%Ss'
LOG_DATE_FORMAT = '%Y/%m/%d %I:%M:%S %p'
LOG_FORMAT = ("tarsnap_update:{base} %(asctime)s [%(levelname)-5.5s] "
              "%(message)s")
MAX_RETRY = 5
RETRY_DELAY = 600
TARSNAP_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

logging.getLogger()
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT.format(base=""),
                    datefmt=LOG_DATE_FORMAT)


def get_backup_list(base):
    """Get list from tarsnap and filter by base"""
    # Get the backup list from the tarsnap server
    cmd = "tarsnap -v --list-archives"
    for idx in range(MAX_RETRY + 1):
        try:
            backups_raw = subprocess.check_output(shlex.split(cmd),
                                                  universal_newlines=True)
            break
        except subprocess.CalledProcessError as err:
            if err.returncode != -11 or idx == MAX_RETRY:
                raise err
            else:
                time.sleep(RETRY_DELAY)

    backups_raw = backups_raw.splitlines()
    backups_raw = [backup.split('\t') for backup in backups_raw]
    backups_raw = [backup for backup in backups_raw
                   if re.match(base, backup[0])]
    backups_raw.sort(key=lambda backup: backup[1], reverse=True)

    backups = [backup[0] for backup in backups_raw]
    times = [datetime.datetime.strptime(backup[1], TARSNAP_DATE_FORMAT)
             for backup in backups_raw]

    return (backups, times)


def remove_backups(base):
    """Remove directories in deletions from destination"""
    aging_params = [(datetime.timedelta(ap[0]), datetime.timedelta(ap[1]))
                    for ap in AGING_PARAMS]
    backups, times = get_backup_list(base)
    keep_idx = list_filters.space_by_span(times, aging_params)
    deletions = [backups[idx] for idx in range(len(backups))
                 if idx not in keep_idx]
    logging.info('Deleting expired backups: %s', ', '.join(deletions))
    cmd = 'tarsnap -d -f "{}"'.format(' -f '.join(deletions))
    for _ in range(MAX_RETRY):
        retcode = subprocess.call(shlex.split(cmd))
        if retcode == 0:
            break
        else:
            time.sleep(RETRY_DELAY)


def run_backup(target, base):
    """Run the tarsnap backup"""
    date_str = datetime.datetime.now().strftime(DATE_FORMAT)
    archive = '{base}: {date}'.format(base=base,
                                      date=date_str)
    cmd = 'tarsnap -c -f "{archive}" "{target}"'
    cmd = cmd.format(archive=archive, target=target)
    logging.info('Running backup: %s', cmd)
    exit_code = subprocess.call(shlex.split(cmd))
    return exit_code


def main(target, delay=0, buff=0, aging_params=None, name=None):
    """Main backup logic"""
    if aging_params is not None:
        # pylint: disable=global-statement
        if any(len(1) != 2 for l in aging_params):
            raise ValueError(('Invalid aging input. All entries must lists of '
                              'two floats.'))
        else:
            global AGING_PARAMS
            AGING_PARAMS = aging_params
        # pylint: enable=global-statement
    if name is not None:
        base = name
    else:
        base = os.path.basename(target)
    logger = logging.getLogger()
    for handler in logger.handlers:
        log_fmt = logging.Formatter(LOG_FORMAT.format(base=base + ':'),
                                    datefmt=LOG_DATE_FORMAT)
        handler.setFormatter(log_fmt)
    logging.info('Backup started for target %s with base %s', target, base)

    buff = buff - delay/60
    if buff > 0:
        _, backup_times = get_backup_list(base)
        last_backup_time = backup_times[0]
        if (datetime.datetime.now() - last_backup_time <
                datetime.timedelta(0, buff*60)):
            logging.info(('Last backup at %s occurred within buffer of %d '
                          'minutes. Skipping backup'),
                         last_backup_time.strftime('%Y/%m/%d %H:%M:%S'),
                         buff)
            logging.info('Process completed')
            return

    time.sleep(delay)

    # Attempt to run backup until it succeeds or fails too many times (e.g. due
    # to lack of network connection)
    for attempt in range(MAX_RETRY):
        exit_code = run_backup(target, base)
        if exit_code == 0:
            remove_backups(base)
            break
        else:
            if attempt < MAX_RETRY - 1:
                logging.info('Backup failed. Retrying in %d', RETRY_DELAY)
                time.sleep(RETRY_DELAY)
            else:
                logging.info('Max number of retries exceeded.')

    logging.info('Process completed')


if __name__ == '__main__':
    import argparse
    # pylint: disable=invalid-name
    parser = argparse.ArgumentParser('Backup files via tarsnap')
    parser.add_argument('target',
                        help=('Target directory to backup.'))
    parser.add_argument('--delay', type=int, default=0,
                        help=('Delay in seconds before starting backup '
                              '(counted from time of first successful '
                              'response from tarsnap server)'))
    parser.add_argument('--buffer', type=int, default=0,
                        help=('Time in minutes that must have elapsed for a '
                              'backup to be run (otherwise process exits '
                              'immediately)'))
    parser.add_argument('--aging', '-a', type=float, default=None, nargs='*',
                        action='append',
                        help=('Aging parameters pair to append to list of '
                              'aging parameters. First number is the spacing '
                              'to keep between backups and the second is the '
                              'oldest backup for which the spacing applies. '
                              'Both numbers are in days. Rules should be '
                              'applied as separate -a options applied in '
                              'order of newest to oldest and override the '
                              'default set.'))
    parser.add_argument('--name', '-n', type=str, default=None,
                        help=('String to use when creating backup name'))
    args = parser.parse_args()
    # pylint: enable=invalid-name
    main(os.path.abspath(args.target), delay=args.delay, buff=args.buffer,
         aging_params=args.aging, name=args.name)
