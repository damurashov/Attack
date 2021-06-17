import sys

import numpy as np
from queue import Queue
from PySide2.QtCore import Signal, Slot, QThread, QObject


from yolodetector import YoLoDetector
from mottracker   import MotTracker
from deep_sort_pytorch.deep_sort.sort.kalman_filter import  KalmanFilter



class DetectorThread(QThread):

    frame_processed = Signal(dict)

    def __init__(self, frameQueue, opts):

        super().__init__()

        self.taskQueue    = frameQueue
        self.yoloDetector = YoLoDetector(opts)
        self.motTracker   = MotTracker(opts)
        self._propogate   = opts.propagate_objects
        self._run_flag = True

    def run(self):

        while self._run_flag:
            try:
                data = self.taskQueue.get()
                #data = data_queue['data']

                if isinstance(data, str):
                    self._run_flag = False

                bboxes, confs, _ = self.yoloDetector.detect(np.copy(data), True)
                bboxes, identities = self.motTracker.track(np.copy(data), bboxes, confs)

                result = {'topic': 'objects','data': ([], [], np.copy(data))}

                if len(bboxes) > 0:
                   result['data'] = (bboxes, identities, np.copy(data))

                if self._propogate:
                   tracks_data =[]
                   for track in self.motTracker.deepsort.tracker.tracks:
                       if not track.is_confirmed() or track.time_since_update > 1:
                           continue
                       tracks_data.append((np.copy(track.mean), np.copy(track.covariance), track.track_id))
                   tracks_data = np.array(tracks_data)
                   result['tracks'] = np.copy(tracks_data)

                self.frame_processed.emit(result)
                self.taskQueue.task_done()
            except Exception as e:
                self.taskQueue.task_done()
                print('object detection error {}' + str(e))


    def stop(self):
        self._run_flag = False
        self.terminate()
        self.wait()


class ObjectDetector(QObject):

    frame_processed = Signal(dict)

    def __init__(self, roi, area_threshold, sz_threshold, opts):

        super().__init__()
        self.frameQueue    = Queue(1)
        self.detector      = DetectorThread(self.frameQueue, opts)
        self.detector.frame_processed.connect(self.detector_update)

        self._propagate = opts.propagate_objects

        self.kf           = KalmanFilter()
        self.tracks       = []
        self.detectROI    = roi
        self.area_threshold  = area_threshold
        self.minRectDim      = min(sz_threshold)
        self.maxRectDim      = max(sz_threshold)

        self.detector.start()


    def detect(self, frame):
        if not self.frameQueue.full():
            self.frameQueue.put(frame)

        if self._propagate:
            if len(self.tracks) ==0:
                return [], []

            bboxes, identities = [], []

            tracks = []
            for mean, covariance, id in self.tracks:
                pmean, pcovariance =self.kf.predict(mean, covariance)
                bboxes.append(self._to_tlwh(pmean))
                identities.append(id)
                tracks.append((pmean, pcovariance, id))
            self.tracks = tracks
            return np.array(bboxes), np.array(identities)


    def stop(self):
        self.detector.stop()

    @Slot(dict)
    def detector_update(self, detections):

        bboxes, identities, frame = detections['data']

        if len(bboxes) == 0 or len(identities) ==0:
            self.tracks = []
            return

        msk, trboxes = self.filt_by_size(bboxes)

        if len(trboxes) == 0:
            self.tracks =[]
            return

        msk_c = self.filt_by_center(trboxes)

        if len(msk_c) == 0:
            self.tracks =[]
            return

        msk = np.where(msk==msk_c)
        if msk is None:
            self.tracks = []
            return

        trboxes, identities  =trboxes[msk[0]], identities[msk[0]]


        if not self._propagate:
            self.frame_processed.emit({'topic': 'objects',
                                       'data': (trboxes, identities, frame)})
            return

        tracks  = detections['tracks']
        self.tracks = tracks[msk]


    def filt_by_center(self, candidates):

        bbox_tl, bbox_br = self.detectROI[:2], self.detectROI[:2] + self.detectROI[2:]

        candidates_tl = candidates[:, :2]
        candidates_br = candidates[:, :2] + candidates[:, 2:]

        tl = np.c_[np.maximum(bbox_tl[0], candidates_tl[:, 0])[:, np.newaxis],
                   np.maximum(bbox_tl[1], candidates_tl[:, 1])[:, np.newaxis]]
        br = np.c_[np.minimum(bbox_br[0], candidates_br[:, 0])[:, np.newaxis],
                   np.minimum(bbox_br[1], candidates_br[:, 1])[:, np.newaxis]]
        wh = np.maximum(0., br - tl)

        area_intersection = wh.prod(axis=1)
        area_candidates = candidates[:, 2:].prod(axis=1)
        trackeable_area = area_intersection / area_candidates
        msk = np.where(trackeable_area > self.area_threshold)
        if msk is None:
            return []

        return msk[0]


    def filt_by_size(self, bboxes):
        if len(bboxes) == 0:
            return [], []
        msk = []
        out_boxes =[]
        for idx, box in enumerate(bboxes):
            x1, y1, w, h = [int(i) for i in box]
            out_boxes.append([x1, y1, w - x1, h - y1])
            if max(w-x1, h-y1) < self.maxRectDim and min(w-x1, h-y1) > self.minRectDim:
                msk.append(idx)
        return np.array(msk), np.array(out_boxes)

    def _to_tlwh(self, mean):
        rect =  mean[:4].copy()
        rect[2] *= rect[3]
        rect[:2] -= rect[2:] / 2
        return rect




