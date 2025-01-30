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

import argparse
import logging
import os

from tarsnap_update.backups import run_managed_backup


def main(args_list: None | list[str] = None):
    """Main command line interface entry point"""
    # pylint: disable=invalid-name
    parser = argparse.ArgumentParser("Backup files via tarsnap")
    parser.add_argument("target", help="Target directory to backup.")
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        help=(
            "Delay in seconds before starting backup "
            "(counted from time of first successful "
            "response from tarsnap server)"
        ),
    )
    parser.add_argument(
        "--buffer",
        type=int,
        default=0,
        help=(
            "Time in minutes that must have elapsed for a "
            "backup to be run (otherwise process exits "
            "immediately)"
        ),
    )
    parser.add_argument(
        "--aging",
        "-a",
        type=float,
        default=None,
        nargs="*",
        action="append",
        help=(
            "Aging parameters pair to append to list of "
            "aging parameters. First number is the spacing "
            "to keep between backups and the second is the "
            "oldest backup for which the spacing applies. "
            "Both numbers are in days. Rules should be "
            "applied as separate -a options applied in "
            "order of newest to oldest and override the "
            "default set."
        ),
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=None,
        help=("String to use when creating backup name"),
    )
    args = parser.parse_args(args_list)
    # pylint: enable=invalid-name

    logging.basicConfig(
        level=logging.INFO,
        format="tarsnap_update:%(name)s %(asctime)s [%(levelname)-5.5s] %(message)s",
        datefmt="%Y/%m/%d %I:%M:%S %p",
    )

    run_managed_backup(
        os.path.abspath(args.target),
        delay=args.delay,
        buff=args.buffer,
        aging_params=args.aging,
        name=args.name,
    )
