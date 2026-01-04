#!/usr/bin/env python3
"""Short script to create a new tarsnap backup"""

#  This file is part of tarsnap_update
#
# tarsnap_update is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# tarsnap_update is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tarsnap_update.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2025, Will Shanks

import datetime
import logging
import os
import re
import shutil
import subprocess
import time
from itertools import repeat
from pathlib import Path

from tarsnap_update.list_filters import space_by_span


__all__ = ["run_managed_backup"]

AGING_PARAMS = ((0.5 / 24, 2), (1, 14), (7, 60), (30, 730), (365, -1))
DATE_FORMAT = "%Y-%m-%d_%Hh%Mm%Ss"
MAX_RETRY = 5
RETRY_DELAY = 600
TARSNAP_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger(__name__)


def lookup_tarsnap_bin() -> str:
    """Find the tarsnap binary

    This is a workaround to Bluefin using Homebrew for tarsnap where the bin/
    directory is not in the systemd PATH.
    """
    tarsnap_bin = shutil.which("tarsnap") or "/home/linuxbrew/.linuxbrew/bin/tarsnap"
    if not Path(tarsnap_bin).exists():
        raise RunetimeError("Could not find tarsnap executable!")

    return tarsnap_bin


def get_backup_list(base):
    """Get list from tarsnap and filter by base"""
    # Get the backup list from the tarsnap server
    tarsnap_bin = lookup_tarsnap_bin()
    cmd = [tarsnap_bin, "-v", "--list-archives"]
    for idx in range(MAX_RETRY + 1):
        try:
            backups_raw = subprocess.check_output(cmd, universal_newlines=True)
            break
        except subprocess.CalledProcessError as err:
            if err.returncode not in [1, -11] or idx == MAX_RETRY:
                raise err
            logger.info("list-archives exit code: %d", err.returncode)
            time.sleep(RETRY_DELAY)

    backups_raw = backups_raw.splitlines()
    backups_raw = [backup.split("\t") for backup in backups_raw]
    backups_raw = [backup for backup in backups_raw if re.match(base, backup[0])]
    backups_raw.sort(key=lambda backup: backup[1], reverse=True)

    backups = [backup[0] for backup in backups_raw]
    times = [
        datetime.datetime.strptime(backup[1], TARSNAP_DATE_FORMAT)
        for backup in backups_raw
    ]

    return (backups, times)


def remove_backups(base, aging_params):
    """Remove directories in deletions from destination"""
    aging_params_td = [
        (datetime.timedelta(ap[0]), datetime.timedelta(ap[1])) for ap in aging_params
    ]
    backups, times = get_backup_list(base)
    keep_idx = space_by_span(times, aging_params_td, reverse=True)
    deletions = [backups[idx] for idx in range(len(backups)) if idx not in keep_idx]
    if len(deletions) == 0:
        logger.info("No expired backups at this time")
        return
    logger.info("Deleting expired backups: %s", ", ".join(deletions))
    args = [arg for f_d in zip(repeat("-f"), deletions) for arg in f_d]
    tarsnap_bin = lookup_tarsnap_bin()
    cmd = [tarsnap_bin, "-d"] + args
    for _ in range(MAX_RETRY):
        retcode = subprocess.call(cmd)
        if retcode == 0:
            break
        time.sleep(RETRY_DELAY)


def run_single_backup(target, base):
    """Run the tarsnap backup"""
    date_str = datetime.datetime.now().strftime(DATE_FORMAT)
    archive = f"{base}: {date_str}"
    tarsnap_bin = lookup_tarsnap_bin()
    cmd = [tarsnap_bin, "-c", "-f", archive, target]
    logger.info("Running backup: %s", ' '.join(cmd))
    exit_code = subprocess.call(cmd)
    return exit_code


def run_managed_backup(target, delay=0, buff=0, aging_params=None, name=None):
    """Run a backup and prune old backups with failure handling"""
    aging_params = aging_params if aging_params is not None else AGING_PARAMS
    if any(len(p) != 2 for p in aging_params):
        raise ValueError(
            ("Invalid aging input. All entries must lists of two floats.")
        )
    if name is not None:
        base = name
    else:
        base = os.path.basename(target)
    logger.info("Backup started for target %s with base %s", target, base)

    buff = buff - delay / 60
    if buff > 0:
        _, backup_times = get_backup_list(base)
        last_backup_time = backup_times[0]
        if datetime.datetime.now() - last_backup_time < datetime.timedelta(
            0, buff * 60
        ):
            logger.info(
                (
                    "Last backup at %s occurred within buffer of %d "
                    "minutes. Skipping backup"
                ),
                last_backup_time.strftime("%Y/%m/%d %H:%M:%S"),
                buff,
            )
            logger.info("Process completed")
            return

    time.sleep(delay)

    # Attempt to run backup until it succeeds or fails too many times (e.g. due
    # to lack of network connection)
    for attempt in range(MAX_RETRY):
        exit_code = run_single_backup(target, base)
        if exit_code == 0:
            remove_backups(base, aging_params)
            break
        if attempt < MAX_RETRY - 1:
            logger.info("Backup failed. Retrying in %d", RETRY_DELAY)
            time.sleep(RETRY_DELAY)
        else:
            logger.info("Max number of retries exceeded.")

    logger.info("Process completed")
