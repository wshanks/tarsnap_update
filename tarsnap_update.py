#!/usr/bin/env python3
"""Short script to create a new tarsnap backup"""
import datetime
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
TARSNAP_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_RETRY = 5
RETRY_DELAY = 600


def get_backup_list(base):
    """Get list from tarsnap and filter by base"""
    cmd = "tarsnap -v --list-archives"
    backups_raw = subprocess.check_output(shlex.split(cmd),
                                          universal_newlines=True)
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
    for backup in deletions:
        cmd = 'tarsnap -d -f "{}"'.format(backup)
        subprocess.call(shlex.split(cmd))


def run_backup(target):
    """Run the tarsnap backup"""
    date_str = datetime.datetime.now().strftime(DATE_FORMAT)
    base = os.path.basename(target)
    archive = '{base}: {date}'.format(base=base,
                                      date=date_str)
    cmd = 'tarsnap -c -f "{archive}" "{target}"'
    cmd = cmd.format(archive=archive, target=target)
    idx = 0
    while idx < MAX_RETRY:
        exit_code = subprocess.call(shlex.split(cmd))
        if exit_code == 0:
            break
        else:
            time.sleep(RETRY_DELAY)
            idx = idx + 1

    remove_backups(base)


if __name__ == '__main__':
    import argparse
    # pylint: disable=invalid-name
    parser = argparse.ArgumentParser('Backup files via tarsnap')
    parser.add_argument('target',
                        help=('Target directory to backup.'))
    args = parser.parse_args()
    # pylint: enable=invalid-name
    run_backup(os.path.abspath(args.target))
