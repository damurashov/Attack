from pioneer_sdk import Pioneer
import numpy as np
import cv2
import time

pioneer_mini = Pioneer()


def img_decorate_with_text(image, text, org=(50, 50,)):
	font = cv2.QT_FONT_NORMAL
	font_scale = 1
	color = (0, 255, 0)
	thickness = 1
	image = cv2.putText(image, text, org, font,
		font_scale, color, thickness, cv2.LINE_AA)
	return image


class FpsCounter:

	PROBE_TIME_SECONDS = 2.0

	def __init__(self):
		self.time_origin = time.time()
		self.frames_overall = 0
		self.time = time.time()
		self.count = 0

	def __reset(self):
		self.count = 0
		self.time = time.time()

	def inc(self) -> float or None:
		"""
		:return: FPS, if ready. None otherwise
		"""
		self.count += 1
		self.frames_overall += 1

		if time.time() - self.time_origin > 10:
			self.frames_overall = 0
			self.time_origin = time.time()

		time_diff = time.time() - self.time
		if time_diff > FpsCounter.PROBE_TIME_SECONDS:
			fps = self.count / time_diff if self.count > 0 else 0
			self.__reset()
			return fps
		else:
			return None

	def fps_mean(self) -> float:
		return self.frames_overall / (time.time() - self.time_origin)


if __name__ == '__main__':
	fps_counter = FpsCounter()
	prev_fps = 0
	while True:
		camera_frame = pioneer_mini.get_raw_video_frame()
		if camera_frame is not None:
			camera_frame = cv2.imdecode(np.frombuffer(camera_frame, dtype=np.uint8), cv2.IMREAD_COLOR)

		fps = fps_counter.inc()
		if fps is not None:
			prev_fps = fps

		camera_frame = img_decorate_with_text(camera_frame, f'fps: {prev_fps}')
		camera_frame = img_decorate_with_text(camera_frame, f'fps_mean: {fps_counter.fps_mean()}', (50,100,))

		cv2.imshow('pioneer_camera_stream', camera_frame)

		key = cv2.waitKey(1)
		if key == 27:  # esc
			print('esc pressed')
			cv2.destroyAllWindows()
			exit(0)