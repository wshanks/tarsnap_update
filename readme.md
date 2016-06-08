Basic description
-----------------
This repo contains a Python 3 script that can be used for running regular tarsnap backups that expire in a geometrically spaced fashion. It also contains service files for running the script as a systemd timer.

Run `tarsnap_update.py -h` for the most updated descriptions of the available options.

By default, backups are named using the date and the base name of the target directory being backed up. A string can be specified with the `--name` option to be used instead of the target's base name. This name is used to filter the list of archives in the tarsnap account before old backups are pruned (so multiple targets can be backed up to the same tarsnap account without impacting each other's retention).

The retention rules are a list of tuples where the first element is the spacing that should be kept between backups and the second element is the oldest backup for which the spacing applies. The list should be in order from newest to oldest. Both numbers are in days. Setting the oldest backup to -1 means that that backup spacing will be used for all backups older than the previous rule. (There is a default set of rules that can be used rather than passing these in as arguments).

Setup for use with systemd
--------------------------
Modify ExecStart in tarsnap.service to run tarsnap_update on correct target. Also, make sure path to tarsnap_update is correct, and set the delay and start buffers as desired.
	cp tarsnap.timer tarsnap.service ~/.config/systemd/user
	systemctl --user enable tarsnap.timer
	systemctl --user enable tarnsape.service
	systemctl --user start tarsnap.timer 

License
-------
tarsnap_update is licensed under the GNU Public License version 3 (GPLv3).
