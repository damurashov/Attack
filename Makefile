ifeq ($(OS), Windows_NT)
	PYTHON3 := py
else
	PYTHON3 := python3.7
endif


PYTHON3_VENV := $(abspath ./venv/bin/python3)
PIP3_VENV := $(abspath ./venv/bin/pip3)
define DEPS
----------------------------------------
The following dependencies must be satisfied:
----------------------------------------
	---
	- python 3.7 or newer, and complementary tools
	  on ubuntu, run sudo apt update && sudo apt install python3.7*,
	  or check Python\'s official site: https://www.python.org/downloads/
	- nvidia cuda toolkit
	  run sudo apt install nvidia-cuda-toolkit on ubuntu,
	  or check out NVidia\'s official site: https://developer.nvidia.com/cuda-toolkit
	  and get the option that suits you
	- Cygwin (on Windows): https://cygwin.com/install.html
	- You will also need a C++ compiler to be used by Cython
endef
export DEPS

venv:
	@echo "$$DEPS"

	#----------------------------------------
	# Creating venv
	#----------------------------------------
	$(PYTHON3) -m venv ./venv

requirements: venv
	#----------------------------------------
	# Installing dependencies
	#----------------------------------------
	cat requirements.txt | xargs -n 1 $(PIP3_VENV) install
.PHONY: requirements

deps_compile: venv
	#----------------------------------------
	# Following the instructions from https://github.com/StrangerZhang/pyECO, 
	#----------------------------------------
	-cd ./lib/eco/features && $(PYTHON3_VENV) ./setup.py build --inplace

	#----------------------------------------
	# Following the instructions from https://github.com/fengyang95/pyCFTrackers
	#----------------------------------------
	-cd ./lib/pysot/utils && $(PYTHON3_VENV) ./setup.py build_ext --inplace
.PHONY: deps_compile

deploy: requirements deps_compile
.PHONY: deploy

# Run entry point
run: clean
	$(PYTHON3_VENV) ./qt_control.py

# Plot a time / engage status chart (for debugging purposes)
plot_engage:
	$(PYTHON3_VENV) /plot_log.py ./log-engage-* &
.PHONY: plot_engage

# Plot a time / rc status chart
plot_rc:
	$(PYTHON3_VENV) ./plot_log.py ./log-rc-* &
.PHONY: plot_rc

# Plot a time / visual threshold status. The visual threshold denotes an 
# "edge" value. Once it's been crossed, the UAV is clear to engage
plot_threshold:
	$(PYTHON3_VENV) ./plot_log.py ./log-threshold-* &
.PHONY: plot_threshold

clean:
	rm -f log-*
.PHONY: clean
