# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 14:06:17 2020

@author: Ali Hamdi; ali.ali@rmit.edu.au
"""

import time
import math
import numpy as np

from scipy.spatial import distance

import torch
from torch import optim, nn
from torchvision import models, transforms

import cv2


import DroTrack.utils.bbox_helper as bbox_helper
import DroTrack.models.adaptive_optical_flow as adaptive_optical_flow
#import DroTrack.utils.config_helper as config
import DroTrack.utils.cnn_features_extraction as cnn
import DroTrack.models.angular_scaling as angular_scaling
import DroTrack.models.FCM as FCM


norm_transf = transforms.Compose([transforms.ToTensor(),
                                  transforms.Normalize(mean =[0.485, 0.456, 0.406],std  =[0.229, 0.224, 0.225])])


class DroTrack:
    def __init__(self, frame, bbox, vgg16_features=None):
        
        self.frame = frame
        self.bbox = bbox
        self.fbbox = bbox
        self.iterator = 0
        
        # Create a mask image for drawing purposes
        self.mask = np.zeros_like(frame)
        
        x1, y1, x2, y2 = bbox_helper.get_bbox_points(bbox)
        self.template = self.frame[y1:y2,x1:x2]

        #self.template_vgg_features = cnn.features(self.template, config.VGG16_model, config.preprocess)

        if vgg16_features is None:
            self.vgg16 = models.vgg16(pretrained=True)
            self.vgg16_features = list(self.vgg16.features)
            self.vgg16_features = nn.Sequential(*self.vgg16_features)
        else:
            self.vgg16_features = vgg16_features
        self.vgg16_features.eval()

        self.template_vgg_features = cnn.features(self.template, self.vgg16_features, norm_transf)

        #print('template distance: {}'.format(distance.cosine(self.template_vgg_features, cnn.features(self.template, self.vgg16_features, norm_transf))))

        # LKT_intialization
        self.prev_corners = adaptive_optical_flow.LKT_intialization(self.frame, self.template, self.bbox)
        
        xs = np.array([x[0] for x in self.prev_corners])
        ys = np.array([x[1] for x in self.prev_corners])

        corners_center = bbox_helper.get_bbox_center([xs.min(), ys.min() , xs.max()-xs.min(), ys.max()-ys.min()])
        center = bbox_helper.get_bbox_center(bbox)
        self.complement_x, self.complement_y = bbox_helper.complement_point(corners_center, center)
        
        self.prev_bbox = self.bbox
        self.prev_frame = self.frame
        self.prev_of_point = bbox_helper.get_bbox_center(bbox)
                
        self.first_scale = self.prev_bbox[3] / float(self.frame.shape[0])
        self.score =1.


    def track(self, frame):
        self.iterator += 1
        start = time.time()
        scale = self.prev_bbox[3] / float(frame.shape[0])

        # Corner for OF
        corners, status, errors = adaptive_optical_flow.otpical_flow_LKT(self.prev_frame, frame, self.prev_corners, self.mask, scale)
        
        current_corners = []
        for i in corners:
            x,y = i.ravel()
            current_corners.append(list(i.ravel()))
           
        ccs = []
        if len(current_corners) > int(50*scale):
            distances = []
            for i in np.arange(len(self.prev_corners)):
                px, py = self.prev_corners[i].ravel()[0], self.prev_corners[i].ravel()[1]
                cx, cy = current_corners[i][0], current_corners[i][1]
                dist = math.sqrt( (cx - px)**2 + (cy - py)**2 )
                distances.append(dist)
    
            for i in range(len(distances)):
                if distances[i] > np.mean(distances)+0.75*np.std(distances) or distances[i] < np.mean(distances)-0.75*np.std(distances):
                    continue
                ccs.append(list(corners[i].ravel()))
        if len(ccs) > 0:
            current_corners = ccs
            
        xs = np.array([x[0] for x in current_corners])
        ys = np.array([y[1] for y in current_corners])
        
        # Temp;;;;;;;
        of_point_center = bbox_helper.get_bbox_center([xs.min(), ys.min() , xs.max()-xs.min(), ys.max()-ys.min()])
        
        corrected_x = int(of_point_center[0] - self.complement_x * (scale / self.first_scale))
        corrected_y = int(of_point_center[1] - self.complement_y * (scale / self.first_scale))
        center = (corrected_x, corrected_y)

        center, final_angle = angular_scaling.out_of_view_correction(frame, center, self.prev_of_point)
                    
        H = frame.shape[0]
        bboxAng = angular_scaling.Angular_Relative_Scaling(final_angle, self.prev_bbox, center, H)
        
        bbox = [center[0]-(self.prev_bbox[2]/2), center[1]-(self.prev_bbox[3]/2), bboxAng[2], bboxAng[3]] 
    
        bbox = angular_scaling.angular_bbox_correction(bbox, frame, self.fbbox)

        # FUZZY
        if self.iterator % 3 == 0:  #TODO check for small values
            try:
                #print('fyzzt clusterinig: {}'.format(self.iterator))
                #PaddedBbox = [bbox[0]-scale*20, bbox[1]-scale*20, bbox[2]+scale*40, bbox[3]+scale*40]
                PaddedBbox = [max(bbox[0]-int(scale*bbox[2]), 0), max(bbox[1]-int(scale*bbox[3]), 0), int(bbox[2]+int(scale*bbox[2])), int(bbox[3]+int(scale*bbox[3]))]
           
                x1, y1, x2, y2 = bbox_helper.get_bbox_points(PaddedBbox)
                fuzzyArea = frame[y1:y2,x1:x2]
                
                n=2
                #fuzzyArea = cv2.cvtColor(fuzzyArea, cv2.COLOR_BGR2GRAY)
                cluster = FCM.FCM(fuzzyArea, n, m=2, 
                                  epsilon=.05, max_iter=2*n, 
                                  kernel_shape='gaussian', kernel_size=9) #uniform, gaussian
                cluster.form_clusters()
                cluster.calculate_scores()
                
                result = cluster.result

                #print('after fyzzy clusterinig: {}'.format(self.iterator))
                #print('scorre .{}'.format(np.float32(result)))

                result = FCM.postFCM (np.float32(result))
                
                x0, y0, x1, y1 = self.best_segment_coord(result, self.template_vgg_features, fuzzyArea, n)
                
                bbox2 = int(PaddedBbox[0]+x0/2), int(PaddedBbox[1]+y0/2), x0/2+x1, y0/2+y1
                center = bbox_helper.get_bbox_center(bbox2)
                bbox3 = np.array(bbox) - np.array(bbox2)
                bbox = np.array(bbox) - bbox3/10
                bbox = FCM.fcm_bbox_correction(bbox, frame)
            except:
                #print (PaddedBbox, bbox)
                pass
     
        extime = time.time() - start
        
        # Now update the previous frame and previous points
        self.prev_bbox = bbox
        self.prev_frame = frame.copy()
        self.prev_corners = np.array(current_corners).reshape(-1,1,2)
        self.prev_of_point = of_point_center

        return bbox, center, extime
    
    def best_segment_coord(self, result, tf, fuzzyArea, n):
        dists_segments = {}
        close_dist = 1.01
        for i in range(n):
           # print('msk==result')
            mask = result == i
            try:
                #print('np.argwhere')
                coords = np.argwhere(mask)
                x0, y0 = coords.min(axis=0)
                x1, y1 = coords.max(axis=0) + 1   # slices are exclusive at the top

                #sf = cnn.features(fuzzyArea[x0:x1, y0:y1], config.VGG16_model, config.preprocess)

                #cv2.imshow('segments', fuzzyArea[x0:x1, y0:y1])
                #cv2.waitKey(10)
                sf = cnn.features(fuzzyArea[x0:x1, y0:y1], self.vgg16_features, norm_transf)

                _dist = distance.cosine(tf, sf)

                if _dist < close_dist:
                   close_dist = _dist

                dists_segments.update({int(_dist): [x0, y0, x1, y1]})
            except:
                continue
        self.score = 1. - close_dist
        #print('best-sim: {}'.format(1. - close_dist))
        return dists_segments[min(dists_segments)]