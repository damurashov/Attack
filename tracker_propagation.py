import cv2
import time
import numpy as np
from queue import Queue

from PySide2.QtCore import Signal, Slot, QThread, QObject
from kalman_filter  import  KalmanFilter, chi2inv95

from pytracker import PyTracker



class TRACKER_STATES(object):
    STATE_TENTATIVE = 1
    STATE_CONFIRMED = 2
    STATE_LOST      = 3


class Tracker(QThread):

    frame_processed  = Signal(np.ndarray)

    def __init__(self, tracker_name, frame, rect, frame_queue, weights=None):

        super().__init__()

        self.tracker = PyTracker(tracker_name, frame, rect, vgg_model=weights)
        self.frame_queue = frame_queue
        self._run_flag = True

    def run(self):

        while self._run_flag:

            frame = self.frame_queue.get()


            if frame is None:
                break

            try:
                bbox, frame  = self.tracker.update(frame)

                if self.tracker.is_tracked:
                    x, y, w, h = bbox
                    bbox = [int(x), int(y), int(w), int(h)]
                    print('tracker box x: {} y: {} w: {} h: {}'.format(x,y,w,h))
                    self.frame_processed.emit(np.array(bbox))

                #time.sleep(.2)
                self.frame_queue.task_done()
            except:
                self._run_flag = False
                self.frame_queue.task_done()
                print('tracker: error occur')


    def stop(self):
        self._run_flag = False
        self.terminate()
        self.wait()



class TrackerPropagation(QObject):

    def __init__(self, frame, rect, opts, propogate=True, weights= None):

        super().__init__()
        print('46464646')
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

        self.tracker = Tracker(opts.tracker_name, frame, rect, self.frame_queue, weights=weights)
        self.tracker.frame_processed.connect(self.tracker_update)
        #self.tracker.frame_processed2.connect(self.tracker_update2)
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
        return self.state == TRACKER_STATES.STATE_LOST

    @Slot(np.ndarray)
    def tracker_update(self, bbox):
        print('update')
        bbox = np.array(bbox)
        if self.kf.gating_distance(self.mean, self.covariance, self._to_xyah(bbox)) < self.threshold:
            self._update(bbox)
    '''
    @Slot(float, float, float, float)
    def tracker_update2(self, x, y, w, h):
        print('update')
        bbox = np.array([x, y, w, h])
        if self.kf.gating_distance(self.mean, self.covariance, self._to_xyah(bbox)) < self.threshold:
            self._update(bbox)
    '''
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
            self.state = TRACKER_STATES.STATE_LOST


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