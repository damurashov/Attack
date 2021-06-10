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

	def reset(self, *args, **kwargs):
		m = self.control["mode"]  # Reset everything but mode
		for k in self.control.keys():
			self.control[k] = 0
		self.control["mode"] = m

	def set(self, key, value):
		self.control[key] = value

	def push(self):
		self.rc_channels(self.control['roll'], self.control['pitch'], self.control['yaw'], self.control['throttle'], self.control['mode'])

	def push_task(self):
		"""
		Should be used as a thread routine
		:return:
		"""
		while True:
			self.push()
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

	def get_threshold(self):
		raise NotImplemented

	def get_normalized_output_horizontal(self):
		raise NotImplemented

	def get_nor

	def _on_target(self):
		pass

	def __init__(self, threshold, frame_size_xy=None):
		RcWrapper.__init__(self)
		self.pid_vertical = PID(AttackStrategy.P_VERTICAL_PID, AttackStrategy.I_VERTICAL_PID, AttackStrategy.D_VERTICAL_PID, AttackStrategy.SETPOINT)
		self.pid_horizontal = PID(AttackStrategy.P_HORIZONTAL_PID, AttackStrategy.I_HORIZONTAN_PID, AttackStrategy.D_HORIZONTAL_PID, AttackStrategy.SETPOINT)

	def

	def on_error_rad(self, offset_yaw, offset_pitch):
		self.threshold = self._threshold_rad
		self.normalized_output = self._normalized_output_rad

		self._on_target()
		pass

	def on_error_px(self, offset_x, offset_y):
		self.threshold = self._threshold_px
		self.normalized_output = self._normalized_output_px

		self._on_target()
		pass

	def on_target_lost(self):
		self.reset()  # Reset rc values, loiter


