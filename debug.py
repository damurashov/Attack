import matplotlib.pyplot as plt
import numpy as np


class RealTimePlot:

	class Data:
		def _cut(self, d):
			return d[-self._n_lags:] if self._n_lags is None or len(d) > self._n_lags else d

		def __init__(self, x, y, line, n_lags):
			assert type(x) is list and type(y) is list and line is not None

			self.x_data = x
			self.y_data = y
			self._line = line
			self._n_lags = n_lags

			self.set_x(self.x_data)
			self.set_y(self.y_data)

		def set_x(self, x):
			self.x_data = self._cut(x)
			self._line.set_xdata(self.x_data)

		def append_x(self, x):
			self.x_data.append(x)
			self.set_x(self.x_data)

		def set_y(self, y):
			self.y_data = self._cut(y)
			self._line.set_ydata(self.y_data)

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
			return True
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


if __name__ == "__main__":
	import random
	import time

	rt_plot = RealTimePlot(50)
	for i in range(0, 100):
		rt_plot.append_data('test1', float(i), random.random())
		rt_plot.append_data('test2', float(i), random.random() * 2)
		rt_plot.append_data('test3', float(i), random.random() - 10)
		# time.sleep(0.02)
