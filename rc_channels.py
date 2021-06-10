#!/usr/bin/python3

from pioneer_sdk import Pioneer
import keyboard
import time


class Control(Pioneer):

	def __init__(self, *args, **kwargs):
		Pioneer.__init__(self, *args, **kwargs)
		self.control = {
			"roll": 0,
			"pitch": 0,
			"yaw": 0,
			"throttle": 0,
			"mode": 2
		}

	def reset(self, *args, **kwargs):
		m = self.control["mode"]
		for k in self.control.keys():
			self.control[k] = 0
		self.control["mode"] = m

	def set(self, key, value):
		self.control[key] = value

	def push(self):
		self.rc_channels(self.control['roll'], self.control['pitch'], self.control['yaw'], self.control['throttle'], self.control['mode'])


if __name__ == "__main__":
	INC = 1.0
	pioneer = Control()
	pioneer.set("mode", 2)

	keyboard.add_hotkey("w", pioneer.set, args=('pitch', INC))
	keyboard.add_hotkey("s", pioneer.set, args=('pitch', -INC))
	keyboard.add_hotkey("d", pioneer.set, args=('roll', INC))
	keyboard.add_hotkey("a", pioneer.set, args=('roll', -INC))
	keyboard.add_hotkey("e", pioneer.set, args=('yaw', INC))
	keyboard.add_hotkey("q", pioneer.set, args=('yaw', -INC))
	keyboard.add_hotkey("0", pioneer.set, args=('mode', 0))
	keyboard.add_hotkey("1", pioneer.set, args=('mode', 1))
	keyboard.add_hotkey("2", pioneer.set, args=('mode', 2))
	keyboard.add_hotkey("up", pioneer.set, args=('throttle', INC))
	keyboard.add_hotkey("down", pioneer.set, args=('throttle', -INC))
	keyboard.add_hotkey("ctrl+a", pioneer.arm)
	keyboard.add_hotkey("ctrl+d", pioneer.disarm)
	# keyboard.on_release(pioneer.reset)

	keys = ('w', 's', 'a', 'd', 'up', 'down', 'q', 'e')
	for k in keys:
		keyboard.on_release_key(k, pioneer.reset, suppress=True)

	pioneer.push()

	while True:
		pioneer.push()
		pioneer.reset()
		time.sleep(0.05)
