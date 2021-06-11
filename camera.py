#!/usr/bin/python3


import numpy as np
import math
import pioneer_sdk
from tracker_propagation import TrackerPropagation, TRACKER_STATES
from PyQt5.QtCore import QObject
import cv2


class Camera(TrackerPropagation):

	def __init__(self, opts):
		QObject.__init__(self)
		self.pioneer = pioneer_sdk.Pioneer()

		img = self.get_frame()

		if img is None:
			raise Exception

		roi = cv2.selectROI("Select ROI", img)

		TrackerPropagation.__init__(self, img, np.array(roi), opts)

		# Close on any button
		if cv2.waitKey(0):
			cv2.destroyWindow("Select ROI")


	def get_frame(self):
		"""
		:return: None, if failed to get one. cv2 frame on success
		"""
		try:
			img = self.pioneer.get_raw_video_frame()
			if img is None:
				return None

			img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)

			return img
		except:
			return None

	@staticmethod
	def _center_positions(bbox, frame_sz, fov, normalize=True):

		if not isinstance(bbox, np.ndarray):
			bbox = np.array(bbox)
		if not isinstance(frame_sz, np.ndarray):
			frame_sz = np.array(frame_sz)
		bbox = bbox.copy()
		bbox = bbox.astype(np.float64)
		bbox[:2] += bbox[2:] / 2.
		dx, dy = bbox[:2]
		frame_sz = frame_sz.copy()
		frame_sz = frame_sz.astype(np.float64)
		frame_sz = frame_sz / 2.
		cx, cy = frame_sz
		positions = np.array([dx - cx, dy - cy, dx - cx, dy - cy, ])
		positions[:2] = positions[:2] * fov
		if normalize:
			positions[2:] = np.array([(dx - cx) / frame_sz[0], (dy - cy) / frame_sz[1]])
			positions[:2] = positions[2:] * math.tanh(fov)
		return positions

	@staticmethod
	def center_positions(bbox, img, normalize=True, type=None):
		assert type in ['angles', 'pixels', None]

		frame_sz = (img.shape[1], img.shape[0])
		fov = 2.*math.atan2(max(frame_sz), max(frame_sz)*1.5)

		pos = Camera._center_positions(bbox, frame_sz, fov, normalize)

		if type == 'angles':
			return pos[:2]
		elif type == 'pixels':
			return pos[2:]

		return pos

	@staticmethod
	def visualize_tracking(img, bbox, state):
		if state == TRACKER_STATES.STATE_CONFIRMED:
			x1, y1, w, h = bbox
			cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), (0, 255, 0), 2)

		if state == TRACKER_STATES.STATE_DELETED:
			cv2.putText(img, 'OBJECT LOST', (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
						1, (255, 0, 255), 2, cv2.LINE_AA)

		cv2.imshow('Camera Stream', img)
