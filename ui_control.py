#!/usr/bin/python3

import threading

import cv2
import debug
import keyboard
from args import getarparser
from camera import Camera
from control import Control
from tracker_propagation import TRACKER_STATES

N_FRAMES_SKIP = 50  # How many frames will be skipped (necessary for buffer purging)


class UiControl(Control):
    def __init__(self):
        super(Control, self).__init__()

        self.tracker = None
        self.__instantiate_key_mappings()

        self.sem_engage_routine = threading.Semaphore(1)
        self.sem_engage_routine.acquire()

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
                if state == TRACKER_STATES.STATE_LOST:
                    self.controller.on_target_lost()
                    debug.FlightLog.add_log_event("tracker lost")
                    cv2.waitKey(0)
                    cv2.destroyWindow(window_name)
                    break

                # Calculate and apply control action
                hv_positions = Camera.center_positions(bbox, img, type=getarparser().parse_args().pid_input)
                self.controller.on_target(hv_positions[0], -hv_positions[1])


if __name__ == "__main__":
    debug.FlightLog.add_log_event("starting")
    ui_control = UiControl()
    ui_control.engage_mode()
    while True:
        cv2.waitKey(1)
