from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort

import torch

class MotTracker(object):

    def __init__(self, opts):
        self.cfg = get_config()
        self.cfg.merge_from_file(opts.config_deepsort)

        self.deepsort = DeepSort(self.cfg.DEEPSORT.REID_CKPT,
                            max_dist=self.cfg.DEEPSORT.MAX_DIST, min_confidence=self.cfg.DEEPSORT.MIN_CONFIDENCE,
                            nms_max_overlap=self.cfg.DEEPSORT.NMS_MAX_OVERLAP,
                            max_iou_distance=self.cfg.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=self.cfg.DEEPSORT.MAX_AGE, n_init=self.cfg.DEEPSORT.N_INIT, nn_budget=self.cfg.DEEPSORT.NN_BUDGET,
                            use_cuda=True)

    def track(self, image, boxes, confidences):

        bbox_xyxy, identities = [], []

        if len(boxes) > 0:
            xywhs = torch.Tensor(boxes)
            confss = torch.Tensor(confidences)
            outputs = self.deepsort.update(xywhs, confss, image)
            if len(outputs) > 0:
                bbox_xyxy = outputs[:, :4]
                identities = outputs[:, -1]
        else:
            self.deepsort.increment_ages()

        return bbox_xyxy, identities

    def reinit(self):
        self.deepsort = DeepSort(self.cfg.DEEPSORT.REID_CKPT,
                            max_dist=self.cfg.DEEPSORT.MAX_DIST, min_confidence=self.cfg.DEEPSORT.MIN_CONFIDENCE,
                            nms_max_overlap=self.cfg.DEEPSORT.NMS_MAX_OVERLAP,
                            max_iou_distance=self.cfg.DEEPSORT.MAX_IOU_DISTANCE,
                            max_age=self.cfg.DEEPSORT.MAX_AGE, n_init=self.cfg.DEEPSORT.N_INIT, nn_budget=self.cfg.DEEPSORT.NN_BUDGET,
                            use_cuda=True)