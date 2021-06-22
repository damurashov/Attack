import cv2
import numpy as np
#import sys
#sys.path.insert(1, './DroTrack')
'''
from lib.utils import get_img_list,get_ground_truthes,APCE,PSR
from cftracker.mosse import MOSSE
from cftracker.csk import CSK
from cftracker.kcf import KCF
from cftracker.cn import CN
from cftracker.dsst import DSST
from cftracker.staple import Staple
from cftracker.dat import DAT
from cftracker.eco import ECO
from cftracker.bacf import BACF
from cftracker.csrdcf import CSRDCF
from cftracker.samf import SAMF
from cftracker.ldes import LDES
from cftracker.mkcfup import MKCFup
from cftracker.strcf import STRCF
from cftracker.mccth_staple import MCCTHStaple
from lib.eco.config import otb_deep_config,otb_hc_config
from cftracker.config import staple_config,ldes_config,dsst_config,csrdcf_config,mkcf_up_config,mccth_staple_config
from DroTrack.models.DroTrack import DroTrack
'''

class PyTracker:

    def __init__(self, tracker_type, init_frame, init_roi, min_score=.21, vgg_model=None):
        '''
        if tracker_type == 'MOSSE':
            self.tracker=MOSSE()
        elif tracker_type=='CSK':
            self.tracker=CSK()
        elif tracker_type=='CN':
            self.tracker=CN()
        elif tracker_type=='DSST':
            self.tracker=DSST(dsst_config.DSSTConfig())
        elif tracker_type=='Staple':
            self.tracker=Staple(config=staple_config.StapleConfig())
        elif tracker_type=='Staple-CA':
            self.tracker=Staple(config=staple_config.StapleCAConfig())
        elif tracker_type=='KCF_CN':
            self.tracker=KCF(features='cn',kernel='gaussian')
        elif tracker_type=='KCF_GRAY':
            self.tracker=KCF(features='gray',kernel='gaussian')
        elif tracker_type=='KCF_HOG':
            self.tracker=KCF(features='hog',kernel='gaussian')
        elif tracker_type=='DCF_GRAY':
            self.tracker=KCF(features='gray',kernel='linear')
        elif tracker_type=='DCF_HOG':
            self.tracker=KCF(features='hog',kernel='linear')
        elif tracker_type=='DAT':
            self.tracker=DAT()
        elif tracker_type=='ECO-HC':
            self.tracker=ECO(config=otb_hc_config.OTBHCConfig())
        elif tracker_type=='ECO':
            self.tracker=ECO(config=otb_deep_config.OTBDeepConfig())
        elif tracker_type=='BACF':
            self.tracker=BACF()
        elif tracker_type=='CSRDCF':
            self.tracker=CSRDCF(config=csrdcf_config.CSRDCFConfig())
        elif tracker_type=='CSRDCF-LP':
            self.tracker=CSRDCF(config=csrdcf_config.CSRDCFLPConfig())
        elif tracker_type=='SAMF':
            self.tracker=SAMF()
        elif tracker_type=='LDES':
            self.tracker=LDES(ldes_config.LDESDemoLinearConfig())
        elif tracker_type=='DSST-LP':
            self.tracker=DSST(dsst_config.DSSTLPConfig())
        elif tracker_type=='MKCFup':
            self.tracker=MKCFup(config=mkcf_up_config.MKCFupConfig())
        elif tracker_type=='MKCFup-LP':
            self.tracker=MKCFup(config=mkcf_up_config.MKCFupLPConfig())
        elif tracker_type=='STRCF':
            self.tracker=STRCF()
        elif tracker_type=='MCCTH-Staple':
            self.tracker=MCCTHStaple(config=mccth_staple_config.MCCTHOTBConfig())
        '''
        if tracker_type=='CSRT-CV':
            self.tracker=cv2.TrackerCSRT_create()
        elif tracker_type=='KCF-CV':
            self.tracker=cv2.TrackerKCF_create()
        elif tracker_type=='MIL-CV':
            self.tracker=cv2.cv2.TrackerMIL_create()
        elif tracker_type =='DroTracker':
            self.tracker = None
        else:
            raise NotImplementedError

        self.min_score = min_score
        self.is_tracked = True
        self.tracker_name = tracker_type
        if self.tracker_name == 'CSRT-CV' or self.tracker_name == 'KCF-CV'\
            or self.tracker_name == 'MIL-CV':
            x, y, w, h = init_roi
            self.tracker.init(init_frame, [int(x), int(y), int(w), int(h)])
        #elif tracker_type != 'DroTracker':
        #    self.tracker.init(init_frame, init_roi)
        #else:
        #    self.tracker = DroTrack(init_frame, init_roi, vgg16_features=vgg_model)

    def update(self, frame, verbose=False):

        if self.tracker_name == 'CSRT-CV' or self.tracker_name == 'KCF-CV'\
            or self.tracker_name == 'MIL-CV':
                success, bbox = self.tracker.update(frame)
                self.is_tracked = success
                return bbox, frame
        '''
        elif self.tracker_name == 'DroTracker':
            bbox, center, exitime = self.tracker.track(frame)

            if self.tracker.score < self.min_score:
                self.is_tracked = False
            if verbose:
                print('tracker: {} conf: {}'.format(self.tracker_name, round(self.tracker.score, 2)))
                cv2.putText(frame, 'tracker: {} conf: {}'.format(self.tracker_name, round(self.tracker.score,3)), (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 244, 0), 2, cv2.LINE_AA)
            return bbox, frame

        else:
            #print('tracker update: ')
            bbox = self.tracker.update(np.copy(frame), vis=True)
            #print('tracker post update')
            score = self.tracker.score
            F_max = np.max(score)
            #print('tracker score')
            #print('tracker: {} conf: {}'.format(self.tracker_name, round(F_max, 2)))
            print(F_max)
            if F_max < self.min_score:
                print('-------------------tracked----false-----------------')
                self.is_tracked = False
            print('is tracked {}'.format(self.is_tracked))
            if verbose is False:
                print('-------------------tracked----done-----------------')
                return bbox, frame


            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            x1, y1, w, h = bbox
            height, width = frame.shape[:2]
            #apce = APCE(score)
            #psr = PSR(score)
            size=self.tracker.crop_size
            score = cv2.resize(score, size)
            score -= score.min()
            score =score/ score.max()
            score = (score * 255).astype(np.uint8)
            score = cv2.applyColorMap(score, cv2.COLORMAP_JET)
            center = (int(x1+w/2),int(y1+h/2))
            x0,y0=center
            x0=np.clip(x0,0,width-1)
            y0=np.clip(y0,0,height-1)
            center=(x0,y0)
            xmin = int(center[0]) - size[0] // 2
            xmax = int(center[0]) + size[0] // 2 + size[0] % 2
            ymin = int(center[1]) - size[1] // 2
            ymax = int(center[1]) + size[1] // 2 + size[1] % 2

            left = abs(xmin) if xmin < 0 else 0
            xmin = 0 if xmin < 0 else xmin
            right = width - xmax
            xmax = width if right < 0 else xmax
            right = size[0] + right if right < 0 else size[0]
            top = abs(ymin) if ymin < 0 else 0
            ymin = 0 if ymin < 0 else ymin
            down = height - ymax
            ymax = height if down < 0 else ymax
            down = size[1] + down if down < 0 else size[1]
            score = score[top:down, left:right]
            crop_img = frame[ymin:ymax, xmin:xmax]
            score_map = cv2.addWeighted(crop_img, 0.6, score, 0.4, 0)
            frame[ymin:ymax, xmin:xmax] = score_map
            debug_frame=cv2.rectangle(frame, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), (255, 0, 0),1)
            cv2.putText(debug_frame, 'tracker: {} conf: {}'.format(self.tracker_name, round(F_max,4)), (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 244, 0), 2, cv2.LINE_AA)
            print('-------------------tracked----done-----------------')
            return bbox, debug_frame
        '''


