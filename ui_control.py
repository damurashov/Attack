#!/usr/bin/python3

from camera import Camera
from controller import AttackStrategyPixels, AttackStrategy, AttackStrategyAngles
import threading
import argparse
from PID import PID
from PyQt5.QtWidgets import QApplication
import keyboard
import cv2
import sys
import time
import datetime
import re
import csv
from tracker_propagation import TRACKER_STATES
import debug
from args import getarparser

from multiprocessing import Process, Pipe


class ParametersPidAngles:
	P_VERTICAL_PID = 1
	I_VERTICAL_PID = 0.1
	D_VERTICAL_PID = 0.05

	P_HORIZONTAL_PID = 1
	I_HORIZONTAL_PID = 0.1
	D_HORIZONTAL_PID = 0.05


class ParametersPidPixels:
	P_VERTICAL_PID = 0.7
	I_VERTICAL_PID = 0.06
	D_VERTICAL_PID = 0.0

	P_HORIZONTAL_PID = 0.7
	I_HORIZONTAL_PID = 0.06
	D_HORIZONTAL_PID = 0.0


SETPOINT = 0  # The deviation should be "0"
SAMPLE_TIME = None  # "dt" gets updated manually
N_FRAMES_SKIP = 50  # How many frames will be skipped (necessary for buffer purging)


class UiControl:
	def __init__(self):
		self.controller = UiControl.__instantiate_controller()
		self.thread_rc_pid = UiControl.__instantiate_thread_rc(self.controller)
		self.tracker = None
		self.__instantiate_key_mappings()

		self.sem_engage_routine = threading.Semaphore(1)
		self.sem_engage_routine.acquire()

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
		keyboard.add_hotkey('ctrl+e', lambda: self.sem_engage_routine.release())

	def __map_rc_channel_toggle(self, kb_key, rc_channel, value, reset_on_release=True):
		keyboard.add_hotkey(kb_key, self.controller.set_rc, args=(rc_channel, value,))
		# keyboard.on_press_key(kb_key, lambda: self.controller.set_rc(rc_channel, value))
		if reset_on_release:
			# keyboard.add_hotkey(kb_key, self.controller.set_rc, args=(rc_channel, 0.0,), trigger_on_release=True)
			keyboard.on_release_key(kb_key.split('+')[-1], lambda e: self.controller.set_rc(rc_channel, 0.0))

	def engage_mode(self):
		while True:
			self.sem_engage_routine.acquire()
			window_name = "Tracking"

			debug.FlightLog.add_log_event("engage mode")

			camera = Camera(self.controller.get_raw_video_frame)
			camera.purge_buffer(N_FRAMES_SKIP)
			while not camera.init_tracker(window_name):
				pass
			# camera.purge_buffer(N_FRAMES_SKIP)

			while True:

				# Visualize tracking
				img = camera.get_frame()
				if img is None:
					continue
				bbox, state = camera.track(img)
				Camera.visualize_tracking(img, bbox, state, window_name)

				# Process tracking state
				if state == TRACKER_STATES.STATE_DELETED:
					self.controller.on_target_lost()
					debug.FlightLog.add_log_event("tracker lost")
					cv2.waitKey(0)
					cv2.destroyWindow(window_name)
					break

				# Calculate and apply control action
				hv_positions = Camera.center_positions(bbox, img, type=getarparser().parse_args().pid_input)
				self.controller.on_target(hv_positions[0], hv_positions[1])


if __name__ == "__main__":
	app = QApplication(sys.argv)
	debug.FlightLog.add_log_event("starting")
	ui_control = UiControl()
	ui_control.engage_mode()
	while True:
		cv2.waitKey(1)
