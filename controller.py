from PID import PID
import pioneer_sdk
import time
import math
from threedvector import Vector
import debug


def clamp(val, min_value, max_value):
	return max(min(max_value, val), min_value)


class RcWrapper(pioneer_sdk.Pioneer):

	def __init__(self, *args, **kwargs):
		pioneer_sdk.Pioneer.__init__(self, *args, **kwargs)
		self.control = {
			"roll": 0.0,
			"pitch": 0.0,
			"yaw": 0.0,
			"throttle": 0.0,
			"mode": 2
		}

	@staticmethod
	def _rc_clamp(val):
		min_value = -1.0
		max_value = 1.0
		return float(max(min(max_value, val), min_value))

	def reset_rc(self, *args, **kwargs):
		for k in self.control.keys():
			if k != "mode":
				self.control[k] = 0.0

	def set_rc(self, key, value):
		assert key in self.control.keys()
		if key == "mode":
			assert value in [0, 1, 2]
			self.control[key] = value
		else:
			self.control[key] = RcWrapper._rc_clamp(value)

	def push_rc(self):
		self.rc_channels(self.control['roll'], self.control['pitch'], self.control['yaw'], self.control['throttle'], self.control['mode'])

	def push_rc_task(self):
		"""
		Should be used as a thread routine
		:return:
		"""
		while True:
			debug.FlightLog.add_log_rc(self)
			self.push_rc()
			time.sleep(0.05)


class AttackStrategy(RcWrapper):

	def __init__(self, pid_vertical: PID,
		pid_horizontal: PID,
		delta_threshold_preliminary=0.0,
		delta_threshold_clean=0.0,
		control_horizontal_range=(-1.0, 1.0,),
		control_vertical_range=(-1.0, 1.0),
		n_iterations_control_lag=0):
		"""
		@param pid_vertical:  -  vertical PID, expected to be pre-initialized
		@param pid_horizontal:  -  horizontal PID, expected to be pre-initialized
		@param delta_threshold_preliminary:  -  If the threshold is met, the copter is clear to engage if a target gets lost
		@param delta_threshold_clean:  -  If the threshold is met, the copter engages right away
		@param n_iterations_control_lag:  -  number of iterations to skip before starting to impose control action.
		@param control_horizontal_range  -  a range regarding to which the control action will be clamped
		@param control_vertical_range  -  a range regarding to which the control action will be clamped
		"""
		RcWrapper.__init__(self)
		self.pid_vertical = pid_vertical
		self.pid_horizontal = pid_horizontal

		self.last_time_seconds = None
		self.last_offset_horizontal = None
		self.target_lost = None

		self.n_iterations_control_lag = int(n_iterations_control_lag)
		self.n_iterations_control_lag_left = self.n_iterations_control_lag

		self.delta_engage_threshold_preliminary = delta_threshold_preliminary
		self.delta_engage_threshold_clean = delta_threshold_clean

		self.control_horizontal_range = control_horizontal_range
		self.control_vertical_range = control_vertical_range

		debug.FlightLog.add_log_event(f'initializing controller, '
			f'control_horizontal_range: {self.control_horizontal_range}, '
			f'control_vertical_range: {self.control_vertical_range} ,'
			f'n_iterations_control_lag: {self.n_iterations_control_lag}, '
			f'delta_threshold clean / preliminary: {self.delta_engage_threshold_clean} / {self.delta_engage_threshold_preliminary}, '
			f'P / I / D vertical: {self.pid_vertical.Kp} / {self.pid_vertical.Ki} / {self.pid_vertical.Kd}, '
			f'P / I / D horizontal: {self.pid_horizontal.Kp} / {self.pid_horizontal.Ki} / {self.pid_horizontal.Kd}, '
		)


	def reset_pid(self):
		self.last_offset_horizontal = None
		self.last_offset_vertical = None
		self.target_lost = None
		self.n_iterations_control_lag_left = self.n_iterations_control_lag

	def engage(self):
		self.reset_rc()
		# self.set_rc('mode', 1)  # Copter is more agile in ALTHOLD mode, we should use this advantage
		self.set_rc('pitch', 0.5)

	def should_engage(self):
		"""
		Will be invoked after every iteration
		"""
		raise NotImplemented

	def get_normalized_output_horizontal(self, offset_horizontal_control):
		"""
		Should use self.last_offset_horizontal
		"""
		raise NotImplemented

	def get_normalized_output_vertical(self, offset_vertical_control):
		"""
		Should use self.last_offset_vertical
		"""
		raise NotImplemented

	def on_target(self, offset_horizontal, offset_vertical):
		# Update the values
		self.last_offset_horizontal = offset_horizontal
		self.last_offset_vertical = offset_vertical
		self.target_lost = False

		if self.should_engage():
			debug.FlightLog.add_log_event("controller -- engaging (target locked)")
			self.engage()
			return

		y_control = clamp(self.get_normalized_output_vertical(self.pid_vertical(offset_vertical)), *self.control_vertical_range)
		x_control = clamp(self.get_normalized_output_horizontal(self.pid_horizontal(offset_horizontal)), *self.control_horizontal_range)

		if self.n_iterations_control_lag_left > 0:
			self.n_iterations_control_lag_left -= 1
			return

		debug.FlightLog.add_log_engage(y_control, x_control, offset_vertical, offset_horizontal)

		self.set_rc("throttle", y_control)
		self.set_rc("yaw", x_control)

	def on_target_lost(self):
		self.target_lost = True

		if self.should_engage():
			debug.FlightLog.add_log_event("controller -- engaging (target lost)")
			self.engage()
		else:
			self.reset_pid()
			self.reset_rc()


class AttackStrategyPixels(AttackStrategy):

	def __init__(self, frame_width=480, frame_height=320, *args, **kwargs):
		AttackStrategy.__init__(self, *args, **kwargs)
		self.frame_width = frame_width
		self.frame_height = frame_height

	def should_engage(self):
		diff = math.sqrt(self.last_offset_vertical ** 2 + self.last_offset_vertical ** 2)  # Plain-simple vector length

		flag = self.target_lost and diff < self.delta_engage_threshold_preliminary
		flag = flag or diff < self.delta_engage_threshold_clean

		debug.FlightLog.add_log_threshold(diff, self.delta_engage_threshold_clean, self.delta_engage_threshold_preliminary, flag, self.target_lost)

		return flag

	def get_normalized_output_horizontal(self, offset_horizontal_control):
		return -offset_horizontal_control

	def get_normalized_output_vertical(self, offset_vertical_control):
		return -offset_vertical_control


class AttackStrategyAngles(AttackStrategy):

	def __init__(self, *args, **kwargs):
		AttackStrategy.__init__(self, *args, **kwargs)

	def should_engage(self):
		# The representation of spherical coordinates used by this lib. agrees with the ISO representation
		# (https://en.wikipedia.org/wiki/Spherical_coordinate_system)
		# We consider X as view direction. Y increases right from us, Z increases up.

		vec_view = Vector(1, 0, 90)  # (1, 0, 0) in cartesian
		vec_target = Vector(1, math.degrees(self.last_offset_horizontal), 90 - math.degrees(self.last_offset_vertical))  # We leave asimuth as is, but invert altitude

		angle_degrees = math.fabs(vec_view.angle(vec_target))

		flag = angle_degrees < self.delta_engage_threshold_preliminary and self.target_lost
		flag = flag or angle_degrees < self.delta_engage_threshold_clean

		return flag

	def get_normalized_output_horizontal(self, offset_horizontal_control_radians):  # Azimuth
		return math.tanh(offset_horizontal_control_radians)

	def get_normalized_output_vertical(self, offset_vertical_control_radians):  # Altitude
		return math.tanh(offset_vertical_control_radians)