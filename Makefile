run: clean
	sudo python3 ./ui_control.py

plot_engage:
	python3 ./plot_log.py ./log-engage-* &

plot_rc:
	python3 ./plot_log.py ./log-rc-* &

clean:
	rm -f log-*

.PHONY: clean
.PHONY: plot
