import argparse
import numpy as np


names = np.array(['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
        'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
        'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard',
        'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
        'teddy bear', 'hair drier', 'toothbrush'])



def getarparser():

	id = np.where(names == 'person')

	parser = argparse.ArgumentParser()

	parser.add_argument('--weights', type=str, default='yolov5/weights/yolov5s.pt', help='model.pt path')
	parser.add_argument('--source', type=str, default='webcam', help='source')
	parser.add_argument('--img_size', type=int, default=256, help='inference size (pixels)')  # 640,#256

	parser.add_argument('--conf_threshold', type=float, default=0.4, help='object confidence threshold')
	parser.add_argument('--iou_threshold', type=float, default=0.5, help='IOU threshold for NMS')

	parser.add_argument('--device', default='cpu', help='cuda device or cpu')  # '0'

	parser.add_argument('--classes', nargs='+', type=int, default=[id[0]], help='filter by class')  # class 0 is person
	parser.add_argument('--agnostic_nms', action='store_true', help='class-agnostic NMS')
	parser.add_argument('--augment', action='store_true', help='augmented inference')

	parser.add_argument('--copter', action='store_true', help='usage copter camera')
	parser.add_argument('--propagate_objects', action='store_true', help='usage propagate objects for detections')

	parser.add_argument('--dummy_rect_selet', action='store_true', help='rand_object_selection')
	parser.add_argument('--config_deepsort', type=str, default='deep_sort_pytorch/configs/deep_sort.yaml')


	parser.add_argument('--min_hits', type=int,  default=3,  help='minimum hits before state tracker will be CONFIRMED')
	parser.add_argument('--max_age',  type=int,  default=5, help='maximum predictes without updates')
	parser.add_argument('--tracker_name', type=str, default='DroTracker', choices=['SAMF',
																			   'BACF', 'MKCFup', 'LDES', 'Staple',
																			   'DroTracker', 'SAMF', 'Staple-CA'])
	parser.add_argument('--pid_input', type=str, default='pixels', choices=['pixels', 'angles'])

	return parser