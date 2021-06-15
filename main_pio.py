import sys
import cv2
import argparse

import numpy as np
import math

import pioneer_sdk

from tracker_propagation import TrackerPropagation, TRACKER_STATES
from PySide2.QtWidgets import QApplication

def getarparser():

    parser = argparse.ArgumentParser()

    parser.add_argument('--min_hits', type=int,  default=3,  help='minimum hits before state tracker will be CONFIRMED')
    parser.add_argument('--max_age',  type=int,  default=10, help='maximum predictes without updates')
    parser.add_argument('--tracker_name', type=str, default='kcf', choices=['csrt', 'kcf', 'mil'])
    return parser

DELAY_SHOW = 5

def center_positions(bbox, frame_sz, fov, normalize=True):

    if not  isinstance(bbox, np.ndarray):
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

    positions = np.array([dx - cx, dy -cy, dx - cx, dy -cy,])

    positions[:2] = positions[:2]*fov

    if normalize:
        positions[:2] = np.tanh(positions[:2])
        positions[2:] = np.array([(dx - cx)/frame_sz[0], (dy - cy)/frame_sz[1]])

    return positions

fov = lambda frame_size : 2.*math.atan2(max(frame_size), max(frame_size)*1.5)

pioneer = pioneer_sdk.Pioneer()


def pioneer_get_frame():
    try:
        cam_frame_jpeg = pioneer.get_raw_video_frame()
        if cam_frame_jpeg is None:
            return None

        cam_frame_jpeg = cv2.imdecode(np.frombuffer(cam_frame_jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)

        return cam_frame_jpeg
    except:
        return None


if __name__ == '__main__':

    opts = getarparser().parse_args()
    app = QApplication(sys.argv)

    # camera = cv2.VideoCapture(0)
    # ret_err, img = camera.read()

    img = None
    while img is None:
        img = pioneer_get_frame()

    frame_sz = (img.shape[1], img.shape[0])
    view_angle = fov(frame_sz)

    roi = cv2.selectROI('select_roi', img)



    if cv2.waitKey(0):
        cv2.destroyWindow('select_roi')

    positions = center_positions(roi, frame_sz, view_angle)

    tracker = TrackerPropagation(img, np.array(roi), opts)

    while True:
        # _, img = camera.read()
        img = pioneer_get_frame()

        if img is None:
            continue

        bbox, state = tracker.track(img)

        if state == TRACKER_STATES.STATE_CONFIRMED:
            x1, y1, w, h = bbox
            cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), (0, 255, 0), 2)
            print(center_positions(bbox, frame_sz, view_angle))

        if state == TRACKER_STATES.STATE_DELETED:
            cv2.putText(img, 'OBJECT LOST', (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow('camera stream', img)
        cv2.waitKey(DELAY_SHOW)





