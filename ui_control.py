#!/usr/bin/python3

from camera import Camera
from controller import AttackStrategyPixels, AttackStrategy, AttackStrategyAngles
import threading
import argparse
from PID import PID
import keyboard
import cv2


class ParametersPidAngles:
	P_VERTICAL_PID = 1
	I_VERTICAL_PID = 0.1
	D_VERTICAL_PID = 0.05

	P_HORIZONTAL_PID = 1
	I_HORIZONTAL_PID = 0.1
	D_HORIZONTAL_PID = 0.05


class ParametersPidPixels:
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
		self.controller = UiControl.__instantiate_controller()
		self.thread_rc_pid = UiControl.__instantiate_thread_rc(self.controller)
		self.tracker = None
		self.__instantiate_key_mappings()

	@staticmethod
	def __instantiate_thread_rc(controller: AttackStrategy):
		thread_rc_pid = threading.Thread(target=controller.push_rc_task)
		thread_rc_pid.start()
		return thread_rc_pid

	@staticmethod
	def __instantiate_controller():
		pid_input = getarparser().parse_args().pid_input

		pid_to_class_mapping = {
			'pixels': (ParametersPidPixels, AttackStrategyPixels),
			'angles': (ParametersPidAngles, AttackStrategyAngles),
		}

		ParametersClass, StrategyClass = pid_to_class_mapping[pid_input]

		pid_vertical = PID(ParametersClass.P_VERTICAL_PID, ParametersClass.I_VERTICAL_PID, ParametersClass.D_VERTICAL_PID, SETPOINT, SAMPLE_TIME)
		pid_horizontal = PID(ParametersClass.P_HORIZONTAL_PID, ParametersClass.I_HORIZONTAL_PID, ParametersClass.D_HORIZONTAL_PID, SETPOINT, SAMPLE_TIME)

		return StrategyClass(pid_vertical, pid_horizontal)

	@staticmethod
	def __instantiate_tracker():  # Initiates engage mode
		return Camera(getarparser().parse_args())

	def __instantiate_key_mappings(self):
		self.__map_rc_channel_toggle('w', 'pitch', 1.0)
		self.__map_rc_channel_toggle('s', 'pitch', -1.0)
		self.__map_rc_channel_toggle('a', 'roll', -1.0)
		self.__map_rc_channel_toggle('d', 'roll', 1.0)
		self.__map_rc_channel_toggle('q', 'yaw', -1.0)
		self.__map_rc_channel_toggle('e', 'yaw', 1.0)
		self.__map_rc_channel_toggle('shift+w', 'throttle', 1.0)
		self.__map_rc_channel_toggle('shift+s', 'throttle', -1.0)
		keyboard.add_hotkey("0", self.controller.set_rc, args=('mode', 0))
		keyboard.add_hotkey("1", self.controller.set_rc, args=('mode', 1))
		keyboard.add_hotkey("2", self.controller.set_rc, args=('mode', 2))
		keyboard.add_hotkey('ctrl+a', self.controller.arm)
		keyboard.add_hotkey('ctrl+d', self.controller.disarm)
		# keyboard.add_hotkey('ctrl+e', self.engage_mode)

	def __map_rc_channel_toggle(self, kb_key, rc_channel, value, reset_on_release=True):
		keyboard.add_hotkey(kb_key, self.controller.set_rc, args=(rc_channel, value,))
		# keyboard.on_press_key(kb_key, lambda: self.controller.set_rc(rc_channel, value))
		if reset_on_release:
			# keyboard.add_hotkey(kb_key, self.controller.set_rc, args=(rc_channel, 0.0,), trigger_on_release=True)
			keyboard.on_release_key(kb_key.split('+')[-1], lambda e: self.controller.set_rc(rc_channel, 0.0))

	def engage_mode(self):
		self.tracker = UiControl.__instantiate_tracker()

		while True:
			img = self.tracker.get_frame()

			if img is None:
				continue

			bbox, state = self.tracker.track(img)
			Camera.visualize_tracking(img, bbox, state)

			hv_positions = Camera.center_positions(bbox, img, type=self.pid_input)
			self.controller.on_target(*tuple(hv_positions))

			key = cv2.waitKey(1)

			if key == 27:  # esc
				break


if __name__ == "__main__":
	ui_control = UiControl()
	while True:
		pass
