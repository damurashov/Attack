from PID import PID
import pioneer_sdk
import time


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

	P_VERTICAL_PID = 1
	I_VERTICAL_PID = 0.1
	D_VERTICAL_PID = 0.05

	P_HORIZONTAL_PID = 1
	I_HORIZONTAN_PID = 0.1
	D_HORIZONTAL_PID = 0.05

	SETPOINT = 0  # We want error be equal zero

	PREMATURE_RAD_THRESHOLD = 10  # Preliminary action threshold. If we lost a target, but reached the minimum threshold, we perform
	TARGET_RAD_THRESHOLD = 10  # The desired action threshold

	PREMATURE_PX_THRESHOLD = 10  # Preliminary action threshold. If we lost a target, but reached the minimum threshold, we perform
	TARGET_PX_THRESHOLD = 10  # The desired action threshold

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

	def get_normalized_output_horizontal(self, offset_horizontal_suggested):
		"""
		Should use self.last_offset_horizontal
		"""
		raise NotImplemented

	def get_normalized_output_vertical(self, offset_vertical_suggested):
		"""
		Should use self.last_offset_vertical
		"""
		raise NotImplemented

	def on_target(self, offset_horizontal, offset_vertical):
		# Update the values
		self.last_offset_horizontal = offset_horizontal
		self.last_offset_vertical = offset_vertical

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
