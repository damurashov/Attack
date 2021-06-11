#!/usr/bin/python3

from camera import Camera
from controller import AttackStrategyPixels, AttackStrategy, AttackStrategyAngles
import threading
import argparse
from PID import PID
import keyboard
import cv2


class ParametersAnglesPid:
	P_VERTICAL_PID = 1
	I_VERTICAL_PID = 0.1
	D_VERTICAL_PID = 0.05

	P_HORIZONTAL_PID = 1
	I_HORIZONTAL_PID = 0.1
	D_HORIZONTAL_PID = 0.05


class ParametersPixelsPid:
	P_VERTICAL_PID = 1
	I_VERTICAL_PID = 0.1
	D_VERTICAL_PID = 0.05

	P_HORIZONTAL_PID = 1
	I_HORIZONTAL_PID = 0.1
	D_HORIZONTAL_PID = 0.05


SETPOINT = 0  # The deviation should be "0"
SAMPLE_TIME = None  # "dt" gets updated manually


def getarparser():

	parser = argparse.ArgumentParser()

	parser.add_argument('--min_hits', type=int,  default=3,  help='minimum hits before state tracker will be CONFIRMED')
	parser.add_argument('--max_age',  type=int,  default=10, help='maximum predictes without updates')
	parser.add_argument('--tracker_name', type=str, default='kcf', choices=['csrt', 'kcf', 'mil'])
	parser.add_argument('--pid_input', type=str, default='pixels', choices=['pixels', 'angles'])
	return parser


class UiControl:
	def __init__(self):
		self.thread_rc_pid = None
		self.controller = None
		self.camera = None
		self.pid_type = None

		self.__instantiate_strategy()  # Control
		self.__instantiate_thread_rc()

	def __instantiate_thread_rc(self, rc_pid: AttackStrategy):
		self.thread_rc_pid = threading.Thread(target=self.controller.push_rc_task)
		self.thread_rc_pid.start()

	def __instantiate_strategy(self):
		opts = getarparser().parse_args()
		self.pid_type = opts.pid_input

		StrategyClass = object
		if self.pid_type == 'pixels':
			StrategyClass = ParametersPixelsPid
		elif self.pid_type == 'angles':
			StrategyClass = ParametersAnglesPid

		pid_vertical = PID(StrategyClass.P_VERTICAL_PID, StrategyClass.I_VERTICAL_PID, StrategyClass.D_VERTICAL_PID, SETPOINT, SAMPLE_TIME)
		pid_horizontal = PID(StrategyClass.P_HORIZONTAL_PID, StrategyClass.I_HORIZONTAL_PID, StrategyClass.D_HORIZONTAL_PID, SETPOINT, SAMPLE_TIME)

		self.controller = StrategyClass(pid_vertical, pid_horizontal)

	def __instantiate_camera(self):  # Initiates engage mode
		opts = getarparser().parse_args()
		self.camera = Camera(opts)

	def __map_rc_channel_toggle(self, kb_key, rc_channel, value, reset_on_release=True):
		keyboard.add_hotkey(kb_key, self.controller.set_rc, args=(rc_channel, value,))
		if reset_on_release:
			keyboard.on_release_key(kb_key, self.controller.reset_rc)

	def engage_mode(self):
		self.__instantiate_camera()

		while True:
			img = self.camera.get_frame()

			if img is None:
				continue

			bbox, state = self.camera.track(img)
			Camera.visualize_tracking(img, bbox, state)

			hv_positions = Camera.center_positions(bbox, img, type=self.pid_type)
			self.controller.on_target(*tuple(hv_positions))

			key = cv2.waitKey(1)

			if key == 27:  # esc
				break

	def __instantiate_key_mappings(self):
		self.__map_rc_channel_toggle('w', 'pitch', 1.0)
		self.__map_rc_channel_toggle('s', 'pitch', -1.0)
		self.__map_rc_channel_toggle('a', 'roll', -1.0)
		self.__map_rc_channel_toggle('d', 'roll', 1.0)
		self.__map_rc_channel_toggle('q', 'yaw', -1.0)
		self.__map_rc_channel_toggle('e', 'yaw', 1.0)
		self.__map_rc_channel_toggle('shift+w', 'throttle', 1.0)
		self.__map_rc_channel_toggle('shift+s', 'throttle', -1.0)
		self.__map_rc_channel_toggle('0', 'mode', 0, False)
		self.__map_rc_channel_toggle('1', 'mode', 1, False)
		self.__map_rc_channel_toggle('2', 'mode', 2, False)
		keyboard.add_hotkey('ctrl+a', self.controller.arm)
		keyboard.add_hotkey('ctrl+d', self.controller.disarm)
		# keyboard.add_hotkey('ctrl+e', self.engage_mode)


