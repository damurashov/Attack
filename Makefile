run: clean
	sudo python3 ./ui_control.py

plot_engage:
	python3 ./plot_log.py ./log-engage-* &

plot_rc:
	python3 ./plot_log.py ./log-rc-* &

plot_threshold:
	python3 ./plot_log.py ./log-threshold-* &

clean:
	rm -f log-*

.PHONY: clean
.PHONY: plot
