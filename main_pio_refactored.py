from camera import Camera
import argparse
from PyQt5.QtWidgets import QApplication
import sys
import cv2


def getarparser():

	parser = argparse.ArgumentParser()

	parser.add_argument('--min_hits', type=int,  default=3,  help='minimum hits before state tracker will be CONFIRMED')
	parser.add_argument('--max_age',  type=int,  default=10, help='maximum predictes without updates')
	parser.add_argument('--tracker_name', type=str, default='kcf', choices=['csrt', 'kcf', 'mil'])
	return parser


if __name__ == "__main__":
	opts = getarparser().parse_args()
	app = QApplication(sys.argv)

	camera = Camera(opts)

	while True:
		img = camera.get_frame()
		if img is None:
			continue
		bbox, state = camera.track(img)
		Camera.visualize_tracking(img, bbox, state)
		cv2.waitKey(5)