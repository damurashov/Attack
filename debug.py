import matplotlib.pyplot as plt
import numpy as np
import csv
import os
import datetime
import time


ENABLE_DEBUG = True


class RealTimePlot:

	class Data:
		def _cut(self, d):
			return d[-self._n_lags:] if self._n_lags is None or len(d) > self._n_lags else d

		def __init__(self, x, y, line, n_lags):
			assert type(x) is list and type(y) is list and line is not None

			self.x_data = x
			self.y_data = y
			self.line = line
			self._n_lags = n_lags

			self.set_x(self.x_data)
			self.set_y(self.y_data)

		def set_x(self, x):
			self.x_data = self._cut(x)
			self.line.set_xdata(self.x_data)

		def append_x(self, x):
			self.x_data.append(x)
			self.set_x(self.x_data)

		def set_y(self, y):
			self.y_data = self._cut(y)
			self.line.set_ydata(self.y_data)

		def append_y(self, y):
			self.y_data.append(y)
			self.set_y(self.y_data)

	def __init__(self, n_lags):
		plt.ion()

		self.data = dict()

		self.figure, self.ax = plt.subplots()
		self.n_lags = n_lags

	def scope_calculate(self):
		"""
		:return: xmin, xmax, ymin, ymax
		"""
		x_all = []
		y_all = []

		for k, v in self.data.items():
			x_all += self.data[k].x_data
			y_all += self.data[k].y_data

		return min(x_all), max(x_all), min(y_all), max(y_all)

	def _try_create_data(self, name_data, x_data, y_data):
		if name_data not in self.data.keys():
			line, = self.ax.plot(x_data, y_data)
			self.data[name_data] = RealTimePlot.Data(x_data, y_data, line, self.n_lags)
			self.data[name_data].line.set_label(name_data)
			return True
		self.ax.legend(bbox_to_anchor=(0.0, 0.0))
		return False

	def set_data(self, name_data, x_data, y_data):
		if not self._try_create_data(name_data, x_data, y_data):  # Already exists
			self.data[name_data].set_x(x_data)
			self.data[name_data].set_y(y_data)
		self.redraw()

	def append_data(self, name_data, x_point, y_point):
		if not self._try_create_data(name_data, [x_point], [y_point]):  # Already exists
			self.data[name_data].append_x(x_point)
			self.data[name_data].append_y(y_point)
		self.redraw()

	def redraw(self):
		xmin, xmax, ymin, ymax = self.scope_calculate()
		if xmin < xmax and ymin < ymax:
			self.ax.set_xlim(xmin, xmax)
			self.ax.set_ylim(ymin, ymax)

		self.figure.canvas.draw()
		self.figure.canvas.flush_events()


def example_real_time_plot():
	import random

	rt_plot = RealTimePlot(50)
	for i in range(0, 100):
		rt_plot.append_data('test1', float(i), random.random())
		rt_plot.append_data('test2', float(i), random.random() * 2)
		rt_plot.append_data('test3', float(i), random.random() - 10)


class Log:
	def __init__(self, file_variant, field_names=None):
		"""
		:param file_variant:  file_path of an existing file (opens it), or file_instance (just uses it), or file_prefix (creates a new file)
		:param field_names:
		:return:
		"""
		self.file_instance = None

		self.file_close_callback = lambda f: None
		if type(file_variant) is str:
			if os.path.isfile(file_variant):
				self.file_instance = open(file_variant, 'r')  # It is a path to a file, open it
				self.file_close_callback = lambda f: f.close()
			else:
				self.file_instance = open(file_variant + datetime.datetime.strftime(datetime.datetime.now(), "%G-%m-%d-%H-%M-%S") + ".csv", 'w')  # It is a prefix for a file, create it
				self.file_close_callback = lambda f: f.close()
		else:
			self.file_instance = file_variant  # It is an instance of a file, use it

		self.field_names = field_names
		self.csv_writer = None

	def __del__(self):
		self.file_close_callback(self.file_instance)

	def to_list(self):
		"""
		Reads data from the file, and represents the result as a list
		"""
		list_instances = []

		try:
			reader = csv.DictReader(self.file_instance, fieldnames=self.field_names)
		except:
			reader = csv.reader()

		for row in reader:
			list_instances.append(dict(row))

		self.file_instance.seek(0, 0)
		return list_instances

	def to_dict(self):
		"""
		Reads data from the file, and represents the result as a dict
		"""
		dict_entries = dict()
		reader = csv.DictReader(self.file_instance, fieldnames=self.field_names)
		for row in reader:
			for k, v in dict(row).items():
				if k in dict_entries.keys():
					dict_entries[k].append(v)
				else:
					dict_entries[k] = []
		self.file_instance.seek(0, 0)
		return dict_entries

	def write(self, row):
		if self.csv_writer is None:
			if self.field_names is not None:
				self.csv_writer = csv.DictWriter(self.file_instance, fieldnames=self.field_names)
				self.csv_writer.writeheader()
			else:
				self.csv_writer = csv.writer(self.file_instance)
				if self.field_names is not None:
					self.csv_writer.writerow(self.field_names)

		assert type(row) in [list, dict]
		if type(self.csv_writer) is csv.DictWriter and type(row) is list:
			d = dict()
			for k, v in zip(self.csv_writer.fieldnames, row):
				d[k] = v
			self.csv_writer.writerow(d)
		else:
			self.csv_writer.writerow(row)


def example_log():
	import sys
	file_variant = sys.argv[1]
	log = Log(file_variant=file_variant)
	print(log.to_list())
	print(log.to_dict())
	log = log.to_dict()
	plot_data(log)

	del log

	log = Log(file_variant="log-events-", field_names=["time", "event"])
	log.write([12, 'echo'])

	del log

	log = Log(file_variant="log-log")
	log.write([21, 13])
	log.write([21, 13])


def plot_data(data: dict, key_x_data=None):
	"""
	Creates a single plot representing all the data
	:key_x_data: Name of the key representing coordinates for the X axis. When 'None' is used, the first key of the
	             data dictionary is considered to be one
	:data: Data to plot
	"""
	fig, ax = plt.subplots()
	x_key = list(data.keys())[0] if key_x_data is None else key_x_data
	x_values = [float(x) for x in data[x_key]]
	data.pop(x_key)

	for v in data.values():
		ax.plot(x_values, [float(iv) for iv in v])

	ax.legend(list(data.keys()))
	plt.show()


class FlightLog:
	log_engage = Log(file_variant="log-engage-", field_names=['time', 'throttle', 'yaw', 'y_error', 'x_error'])
	log_event = Log(file_variant="log-event-", field_names=['time', 'event'])
	log_rc = Log(file_variant="log-rc-", field_names=['time', 'throttle', 'yaw', "pitch", "roll", "mode"])
	time_start_seconds = time.time()

	@staticmethod
	def get_uptime_seconds():
		return time.time() - FlightLog.time_start_seconds

	@staticmethod
	def add_log_engage(controller, offset: list):
		if not ENABLE_DEBUG:
			return
		FlightLog.log_engage.write([FlightLog.get_uptime_seconds(), controller.control["throttle"], controller.control["yaw"], offset[1], offset[0]])

	@staticmethod
	def add_log_event(event):
		if not ENABLE_DEBUG:
			return
		FlightLog.log_event.write([FlightLog.get_uptime_seconds(), str(event)])

	@staticmethod
	def add_log_rc(controller):
		FlightLog.log_rc.write([FlightLog.get_uptime_seconds()] + [controller.control[k] for k in ['throttle', 'yaw', "pitch", "roll", "mode"]])


if __name__ == "__main__":
	example_log()