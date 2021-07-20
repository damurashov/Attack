ifeq ($(OS), Windows_NT)
	PYTHON3 := py
else
	PYTHON3 := python3
endif

venv:
	rm -rf ./venv
	$(PYTHON3) -m venv ./venv;
	. ./venv/bin/activate;
	pip install -r requirements.txt --no-index;

	# Following the instructions from https://github.com/fengyang95/pyCFTrackers
	python ./lib/pysot/utils/setup.py build_ext --inplace;

	# Following the instructions from https://github.com/StrangerZhang/pyECO
	python ./lib/eco/features/setup.py build_ext --inplace;


	@echo The following dependencies must be satisfied:
	@echo - python 3.7 or newer, and complementary tools
	@echo   on ubuntu, run `sudo apt update && sudo apt install python3.7*`,
	@echo   or check Python\'s official site: `https://www.python.org/downloads/`
	@echo - nvidia cuda toolkit
	@echo   run `sudo apt install nvidia-cuda-toolkit` on ubuntu,
	@echo   or check out NVidia\'s official site: `https://developer.nvidia.com/cuda-toolkit`
	@echo   and get the option that suits you
	@echo - Cygwin (on Windows): `https://cygwin.com/install.html`
	@echo - You will also need a C++ compiler to be used by Cython

# Run entry point
run: clean
	$(PYTHON3) ./qt_control.py

# Plot a time / engage status chart (for debugging purposes)
plot_engage:
	$(PYTHON3) /plot_log.py ./log-engage-* &
.PHONY: plot_engage

# Plot a time / rc status chart
plot_rc:
	$(PYTHON3) ./plot_log.py ./log-rc-* &
.PHONY: plot_rc

# Plot a time / visual threshold status. The visual threshold denotes an 
# "edge" value. Once it's been crossed, the UAV is clear to engage
plot_threshold:
	$(PYTHON3) ./plot_log.py ./log-threshold-* &
.PHONY: plot_threshold

clean:
	rm -f log-*
.PHONY: clean
