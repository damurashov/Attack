import cv2
import time
import numpy as np
from kalman_filter import  KalmanFilter, chi2inv95

from queue import Queue
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject

class TRACKER_STATES(object):
    STATE_TENTATIVE = 1
    STATE_CONFIRMED = 2
    STATE_DELETED   = 3

TRACKERS = {
    'csrt':       cv2.TrackerCSRT_create,
    'kcf':        cv2.TrackerKCF_create,
    'mil':        cv2.TrackerMIL_create,
}


class Tracker(QThread):

    frame_processed = pyqtSignal(np.ndarray)

    def __init__(self, tracker_name, frame, rect, frame_queue):

        super().__init__()

        self.tracker = TRACKERS[tracker_name]()
        self.tracker.init(frame, rect)
        self.frame_queue = frame_queue
        self._run_flag = True

    def run(self):

        while self._run_flag:
            print('getting frame')
            frame = self.frame_queue.get()

            if frame is None:
                print('break')
                break


            success, bbox = self.tracker.update(frame)
            if success:
                x, y, w, h = bbox
                self.frame_processed.emit(np.array([x,y,w,h]))
            print('task finished')
            #time.sleep(.2)
            self.frame_queue.task_done()


    def stop(self):
        self._run_flag = False
        self.stop()



class TrackerPropagation(QObject):

    def __init__(self, frame, rect, opts, propogate=True):

        super().__init__()

        self.frame_queue = Queue(1)
        self.kf = KalmanFilter()
        self.threshold = chi2inv95[4]
        self.rect = self._to_xyah(rect)
        self.mean, self.covariance = self.kf.initiate(self.rect)

        self.hits = 1
        self.age = 1
        self.time_since_update = 0
        self.state = TRACKER_STATES.STATE_TENTATIVE
        self.propogate = propogate

        self.tracker = Tracker(opts.tracker_name.lower(), frame, rect, self.frame_queue)
        self.tracker.frame_processed.connect(self.tracker_update)
        self.tracker.start()

        self._n_init = opts.min_hits
        self._max_age = opts.max_age
        self._run_flag = True


    def track(self, frame):
        if not self.frame_queue.full():
            self.frame_queue.put(np.copy(frame))

        if not self.propogate:
            self.frame_queue.join()

        self._predict()
        return self._to_tlwh(), self.state


    def stop(self):
        self.tracker.stop()

    def is_tentative(self):
        return self.state == TRACKER_STATES.STATE_TENTATIVE

    def is_confirmed(self):
        return self.state == TRACKER_STATES.STATE_CONFIRMED

    def is_deleted(self):
        return self.state == TRACKER_STATES.STATE_DELETED

    @pyqtSlot(dict)
    def tracker_update(self, bbox):
        if self.kf.gating_distance(self.mean, self.covariance, self._to_xyah(bbox)) < self.threshold:
            self._update(bbox)

    def _increment_age(self):
        self.age += 1
        self.time_since_update += 1
        self._mark_missed()

    def _predict(self):
        self.mean, self.covariance = self.kf.predict(self.mean, self.covariance)
        self._increment_age()


    def _update(self, rect):
        self.mean, self.covariance = self.kf.update(
            self.mean, self.covariance, self._to_xyah(rect))
        self.hits += 1
        self.time_since_update = 0
        if self.state == TRACKER_STATES.STATE_TENTATIVE and self.hits >= self._n_init:
            self.state = TRACKER_STATES.STATE_CONFIRMED

    def _mark_missed(self):
        if self.time_since_update > self._max_age:
            self.state = TRACKER_STATES.STATE_DELETED


    def _to_xyah(self, rect):
        rect = rect.copy()
        rect = rect.astype(np.float64)
        rect[:2] += rect[2:] / 2
        rect[2] /= rect[3]
        return rect

    def _to_tlwh(self):
        rect = self.mean[:4].copy()
        rect[2] *= rect[3]
        rect[:2] -= rect[2:] / 2
        return rect