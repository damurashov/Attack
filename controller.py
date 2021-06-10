from PID import PID
import pioneer_sdk
import time
import math


class RcWrapper(pioneer_sdk.Pioneer):

	def __init__(self, *args, **kwargs):
		pioneer_sdk.Pioneer.__init__(self, *args, **kwargs)
		self.control = {
			"roll": 0,
			"pitch": 0,
			"yaw": 0,
			"throttle": 0,
			"mode": 2
		}

	def reset_rc(self, *args, **kwargs):
		m = self.control["mode"]  # Reset everything but mode
		for k in self.control.keys():
			self.control[k] = 0
		self.control["mode"] = m

	def set_rc(self, key, value):
		assert key in self.control.keys()
		self.control[key] = value

	def push_rc(self):
		self.rc_channels(self.control['roll'], self.control['pitch'], self.control['yaw'], self.control['throttle'], self.control['mode'])

	def push_rc_task(self):
		"""
		Should be used as a thread routine
		:return:
		"""
		while True:
			self.push_rc()
			time.sleep(0.05)


class AttackStrategy(RcWrapper):

	def __init__(self, pid_vertical: PID, pid_horizontal: PID):
		RcWrapper.__init__(self)
		self.pid_vertical = pid_vertical
		self.pid_horizontal = pid_horizontal

		self.last_time_seconds = None
		self.last_offset_horizontal = None
		self.last_offset_vertical = None
		self.target_lost = None

	def engage(self):
		self.reset_rc()
		self.set_rc('mode', 1)  # Copter is more agile in ALTHOLD mode, we should use this advantage
		self.set_rc('throttle', 1.0)

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

		delta_time_seconds = self.last_time_seconds
		if self.last_time_seconds is None:
			self.last_time_seconds = time.time()

		if delta_time_seconds is not None:
			delta_time_seconds = self.last_time_seconds - delta_time_seconds

		if self.should_engage():
			self.engage()

		self.set_rc('throttle', self.get_normalized_output_vertical(self.pid_vertical(offset_vertical, delta_time_seconds)))
		self.set_rc('yaw', self.get_normalized_output_horizontal(self.pid_horizontal(offset_horizontal, delta_time_seconds)))

	def on_target_lost(self):
		self.target_lost = True

		if self.should_engage():
			self.engage()


class AttackStrategyPixels(AttackStrategy):

	def __init__(self, pid_vertical: PID, pid_horizontal: PID, frame_width, frame_height):
		AttackStrategy.__init__(self, pid_vertical, pid_horizontal)
		self.frame_width = frame_width
		self.frame_height = frame_height

	def should_engage(self):
		preliminary_threshold = 80
		clean_threshold = 40

		diff = math.sqrt(self.last_offset_vertical ** 2 + self.last_offset_vertical ** 2)  # Plain-simple vector length

		flag = self.target_lost and diff < preliminary_threshold
		flag = flag or diff < clean_threshold

		return flag

	def get_normalized_output_horizontal(self, offset_horizontal_control):
		return offset_horizontal_control / self.frame_width

	def get_normalized_output_vertical(self, offset_vertical_control):
		return offset_vertical_control / self.frame_height


class AttackStrategyAngles(AttackStrategy):

	def __init__(self, pid_vertical, pid_horizontal):
		AttackStrategy.__init__(self, pid_vertical, pid_horizontal)

	def should_engage(self):
		
