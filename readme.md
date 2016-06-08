Setup
-----
Modify ExecStart in tarsnap.service to run tarsnap_update on correct target (and make sure path to tarsnap_update is correct).
	cp tarsnap.timer tarsnap.service ~/.config/systemd/user
	systemctl --user enable tarsnap.timer
	systemctl --user enable tarnsape.service
	systemctl --user start tarsnap.timer 
