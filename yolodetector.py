import sys
sys.path.insert(0, './yolov5')

from yolov5.models.experimental import attempt_load
from yolov5.utils.datasets import letterbox
from yolov5.utils.general import check_img_size, non_max_suppression, scale_coords
from yolov5.utils.torch_utils import select_device

import torch
import numpy as np


class YoLoDetector(object):

    def __init__(self, opts):

        self.device = select_device(opts.device)
        self.half =   self.device.type != 'cpu'
        self.augment = opts.augment
        self.conf_threshold = opts.conf_threshold
        self.iou_threshold  = opts.iou_threshold
        self.classes = opts.classes
        self.agnostic_nms = opts.agnostic_nms

        with torch.no_grad():
            self.model = attempt_load(opts.weights, map_location=self.device)
            self.stride = int(self.model.stride.max())  # model stride
            self.img_size = check_img_size(opts.img_size, s=self.stride)
            self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
            if self.half:
                self.model.half()  # to FP16
            if self.device.type != 'cpu':
                self.model(torch.zeros(1, 3, self.img_size, self.img_size).to(self.device).type_as(next(self.model.parameters())))  # run once


    def detect(self, image, cxcywh=False):

        with torch.no_grad():
            img = letterbox(image, self.img_size, stride=self.stride)[0]
            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
            img = np.ascontiguousarray(img)
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0

            if img.ndimension() == 3:
                img = img.unsqueeze(0)

        predictions = self.model(img,augment=self.augment)[0]
        predictions = non_max_suppression(predictions, self.conf_threshold, self.iou_threshold,
                                          classes=self.classes, agnostic=self.agnostic_nms)
        detect_data = []
        bboxes  =[]
        confs  =[]

        for i, det in enumerate(predictions):

            if det is not None and len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], image.shape).round()

                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    detect_data.append((n, self.names[int(c)]))

                for *xyxy, conf, _ in det:
                    if cxcywh == True:
                        x_c, y_c, bbox_w, bbox_h = self.bbox_rel(*xyxy)
                        obj = [x_c, y_c, bbox_w, bbox_h]
                        bboxes.append(obj)
                    else:
                        bboxes.append(self.to_bboxes(*xyxy))
                    confs.append([conf.item()])

        return bboxes, confs, detect_data

    @classmethod
    def to_bboxes(cls, *xyxy):
        bbox_left = min([xyxy[0].item(), xyxy[2].item()])
        bbox_top = min([xyxy[1].item(), xyxy[3].item()])
        bbox_w = abs(xyxy[0].item() - xyxy[2].item())
        bbox_h = abs(xyxy[1].item() - xyxy[3].item())
        return bbox_left, bbox_top, bbox_w, bbox_h
    @classmethod
    def bbox_rel(cls,*xyxy):
        """" Calculates the relative bounding box from absolute pixel values. """
        bbox_left = min([xyxy[0].item(), xyxy[2].item()])
        bbox_top = min([xyxy[1].item(), xyxy[3].item()])
        bbox_w = abs(xyxy[0].item() - xyxy[2].item())
        bbox_h = abs(xyxy[1].item() - xyxy[3].item())
        x_c = (bbox_left + bbox_w / 2)
        y_c = (bbox_top + bbox_h / 2)
        w = bbox_w
        h = bbox_h
        return x_c, y_c, w, h







