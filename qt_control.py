import os
import sys
from enum import Enum

import PySide2
import cv2
import numpy as np
from PySide2.QtCore import QObject, Property, Signal, QThread, QCoreApplication, Slot, QEnum, QSize, QRect
from PySide2.QtGui import QImage, qRed, qGreen, qBlue
from PySide2.QtMultimedia import QMediaObject, QMediaService, QVideoRendererControl, QVideoFrame, QVideoSurfaceFormat, \
    QAbstractVideoSurface, QMediaControl, QAbstractVideoFilter, QVideoFilterRunnable, QAbstractVideoBuffer
from PySide2.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide2.QtWidgets import QApplication

from args import getarparser
from camera import VggExtractor, Camera
from control import Control
from object_detector import ObjectDetector
from pioneer_sdk import Pioneer
from tracker_propagation import TrackerPropagation, TRACKER_STATES


class UAVCameraHandler(QThread):
    on_frame_available = Signal(QImage)

    def __init__(self, pioneer: Pioneer):
        super(UAVCameraHandler, self).__init__()
        self._pioneer = pioneer

    def run(self) -> None:
        while not self.isInterruptionRequested():
            frame = self._pioneer.get_raw_video_frame()
            if frame is None:
                continue

            image = QImage.fromData(frame)
            self.on_frame_available.emit(image)


class UAVRendererControl(QVideoRendererControl):
    def __init__(self, parent: QObject, pioneer: Pioneer):
        super(UAVRendererControl, self).__init__(parent)
        self._surface: QAbstractVideoSurface = None
        self._handler: UAVCameraHandler = None
        self._pioneer = pioneer

    def surface(self) -> QAbstractVideoSurface:
        return self._surface

    def setSurface(self, surface: QAbstractVideoSurface) -> None:
        if self._surface is not None:
            self._handler.on_frame_available.disconnect()
            self._handler.requestInterruption()
            self._handler.deleteLater()
            self._handler = None

        self._surface = surface

        if self._surface is not None:
            self._handler = UAVCameraHandler(self._pioneer)
            self._handler.on_frame_available.connect(self.present_frame)
            self._handler.start()

    def present_frame(self, image: QImage):
        if self._surface is None:
            return

        if self._surface.isActive():
            pixel_format = QVideoFrame.pixelFormatFromImageFormat(image.format())
            current_format = self._surface.surfaceFormat()
            if current_format.pixelFormat() != pixel_format or current_format.frameSize() != image.size():
                self._surface.stop()

        if not self._surface.isActive():
            pixel_format = QVideoFrame.pixelFormatFromImageFormat(image.format())
            video_surface_format = QVideoSurfaceFormat(image.size(), pixel_format)
            self._surface.start(video_surface_format)

        frame = QVideoFrame(image)
        self._surface.present(frame)


class ControlWrapper(QMediaControl):
    def __init__(self):
        super(ControlWrapper, self).__init__()
        self.control = Control()


class UAVCameraService(QMediaService):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(UAVCameraService, cls).__new__(cls)

        return cls.instance

    def __init__(self):
        if UAVCameraService.__initialized is True:
            return

        super(UAVCameraService, self).__init__(None)
        self._control_wrapper: ControlWrapper = ControlWrapper()
        self._video_renderer_control = UAVRendererControl(self, self._control_wrapper.control.controller)
        UAVCameraService.__initialized = True

    def requestControl(self, name: bytes) -> QMediaControl:
        if name == "org.qt-project.qt.videorenderercontrol/5.0":
            return self._video_renderer_control
        elif name == "org.plaz.control/5.0":
            return self._control_wrapper

        return None

    __initialized = False


class UAVCamera(QMediaObject):

    class StateChangeHandler(QThread):
        def __init__(self, parent: QObject, callback):
            super(UAVCamera.StateChangeHandler, self).__init__(parent)
            self._callback = callback

        def run(self) -> None:
            self._callback()

    @QEnum
    class State(Enum):
        Disarmed = 0
        Arming = 1
        Armed = 2
        Disarming = 3

    def __init__(self, parent):
        super(UAVCamera, self).__init__(parent, UAVCameraService())
        self.control_wrapper: ControlWrapper = self.service().requestControl("org.plaz.control/5.0")
        self._state = self.State.Disarmed

    def __get_controller(self):
        return self.control_wrapper.control.controller

    def arm(self):
        assert self._state == self.State.Disarmed
        handler = self.StateChangeHandler(self, self.__get_controller().arm)
        handler.finished.connect(self.__armed)
        handler.start()
        self.__set_state(self.State.Arming)

    def __armed(self):
        self.__set_state(self.State.Armed)

    def disarm(self):
        assert self._state == self.State.Armed
        handler = self.StateChangeHandler(self, self.__get_controller().disarm)
        handler.finished.connect(self.__disarmed)
        handler.start()
        self.__set_state(self.State.Disarming)

    def __disarmed(self):
        self.__set_state(self.State.Disarmed)

    def __set_state(self, state):
        self._state = state
        self.stateChanged.emit()

    def get_state(self):
        return self._state

    stateChanged = Signal()
    state = Property(int, get_state, notify=stateChanged)


class DeclarativeUAVCamera(QObject):

    @QEnum
    class State(Enum):
        Disarmed = UAVCamera.State.Disarmed.value
        Arming = UAVCamera.State.Arming.value
        Armed = UAVCamera.State.Armed.value
        Disarming = UAVCamera.State.Disarming.value

    def __init__(self):
        super(DeclarativeUAVCamera, self).__init__()
        self._camera = UAVCamera(self)
        self._camera.stateChanged.connect(self.stateChanged)

    @Signal
    def mediaObjectChanged(self):
        pass

    def __get_controller(self):
        return self._camera.control_wrapper.control.controller

    @Slot(float)
    def setPitch(self, value: float):
        self.__get_controller().set_rc('pitch', value)

    @Slot(float)
    def setRoll(self, value: float):
        self.__get_controller().set_rc('roll', value)

    @Slot(float)
    def setYaw(self, value: float):
        self.__get_controller().set_rc('yaw', value)

    @Slot(float)
    def setThrottle(self, value: float):
        self.__get_controller().set_rc('throttle', value)

    @Slot()
    def arm(self):
        self._camera.arm()

    @Slot()
    def disarm(self):
        self._camera.disarm()

    @Slot(bool)
    def attack(self, value: bool):
        self.__get_controller().set_rc('mode', 1 if value else 2)

    def _media_object(self):
        return self._camera

    def _state(self):
        return self._camera.get_state().value

    mediaObject = Property(QObject, _media_object, notify=mediaObjectChanged)
    stateChanged = Signal()
    state = Property(int, _state, notify=stateChanged)

class FilterResult(QObject):
    def __init__(self, rects):
        super(FilterResult, self).__init__()
        self._rects = rects

    @Slot(result="QVariantList")
    def rects(self):
        return self._rects


class DetectorRunnable(QVideoFilterRunnable):

    def __init__(self, video_filter):
        super(DetectorRunnable, self).__init__()
        self._video_filter = video_filter
        self._current_frame_size: QSize = None
        self._detector: ObjectDetector = None
        self._opts = getarparser().parse_args()
        self._result = None

    def run(self, input: QVideoFrame, surfaceFormat: QVideoSurfaceFormat, flags: QVideoFilterRunnable.RunFlags) -> QVideoFrame:
        if not input.isValid():
            return input

        if self._current_frame_size != input.size():
            if self._detector is not None:
                self._detector.stop()

            del self._detector
            self._current_frame_size = input.size()

            # Compute ROI and create new detector
            disply_width = self._current_frame_size.width()
            display_height = self._current_frame_size.height()

            tracked_width = int(disply_width - .2 * disply_width)
            tracked_height = int(display_height - .2 * display_height)

            trackable_ROI = np.array([int((disply_width - tracked_width) / 2.),
                                      int((display_height - tracked_height) / 2.),
                                      tracked_width,
                                      tracked_height
                                      ])

            min_ROI_dim = 5
            max_ROI_dim = 600

            self._detector = ObjectDetector(trackable_ROI, .01, (min_ROI_dim, max_ROI_dim), self._opts)

        image = input.image()

        if image.isNull():
            return input

        image: QImage = image.convertToFormat(QImage.Format.Format_RGBA8888)
        frame = np.array(image.constBits())

        width = image.width()
        height = image.height()

        frame = frame.reshape((height, width, 4))
        cv_image: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        bboxes, identifiers = self._detector.detect(cv_image)

        result = []
        for x, y, w, h in bboxes:
            result.append(QRect(x, y, w, h))

        self._result = FilterResult(result)
        self._video_filter.finished.emit(self._result)

        return input


class Detector(QAbstractVideoFilter):

    def __init__(self):
        super(Detector, self).__init__()

    def createFilterRunnable(self) -> PySide2.QtMultimedia.QVideoFilterRunnable:
        return DetectorRunnable(self)

    finished = Signal(QObject, arguments=['e'])


class EngagerRunnable(QVideoFilterRunnable):

    def __init__(self, video_filter):
        super(EngagerRunnable, self).__init__()
        self._video_filter = video_filter
        self._tracker = None
        self._result = None

    def run(self, input: QVideoFrame, surfaceFormat: QVideoSurfaceFormat, flags: QVideoFilterRunnable.RunFlags) -> QVideoFrame:
        video_filter = self._video_filter
        rect = video_filter.get_rect()
        if rect is None:
            return input

        image = input.image()
        image: QImage = image.convertToFormat(QImage.Format.Format_RGBA8888)
        frame = np.array(image.constBits())

        width = image.width()
        height = image.height()

        frame = frame.reshape((height, width, 4))
        cv_image: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        if self._tracker is None:
            padding = 1.5

            box = np.array([rect.x(), rect.y(), rect.width(), rect.height()])

            if int(min(box[2:]) / padding) > 35:  # TODO move to constant (min_ROI_dim)
                x1, y1, w, h = [int(i) for i in box]

                xc = x1 + w / 2
                yc = y1 + h / 2

                w = w / padding
                h = h / padding

                x1 = xc - w / 2 - 1
                y1 = yc - h / 2 - 1
                box = [x1, y1, w, h]

            self._tracker = TrackerPropagation(cv_image, np.array(box), getarparser().parse_args(), weights=VggExtractor().get_weights())
            return input

        bbox, state = self._tracker.track(cv_image)

        control: ControlWrapper = UAVCameraService().requestControl('org.plaz.control/5.0')

        if state == TRACKER_STATES.STATE_LOST:
            control.control.controller.on_target_lost()
            self._video_filter.lost.emit()
            return input

        x, y, w, h = bbox
        self._result = FilterResult([QRect(x, y, w, h)])
        self._video_filter.finished.emit(self._result)

        # Calculate and apply control action

        hv_positions = Camera.center_positions(bbox, cv_image, type=getarparser().parse_args().pid_input)
        control.control.controller.on_target(hv_positions[0], -hv_positions[1])

        return input
    
    
class Engager(QAbstractVideoFilter):
    
    def __init__(self):
        super(Engager, self).__init__()
        self._rect = None

    def createFilterRunnable(self) -> PySide2.QtMultimedia.QVideoFilterRunnable:
        return EngagerRunnable(self)

    def get_rect(self):
        return self._rect

    def set_rect(self, rect: QRect):
        self._rect = rect

    rect = Property(QRect, get_rect, set_rect)
    finished = Signal(QObject, arguments=['e'])
    lost = Signal()


if __name__ == "__main__":
    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'Qt', 'plugins')
    QCoreApplication.addLibraryPath(plugin_path)

    app = QApplication(sys.argv)

    engine = QQmlApplicationEngine()
    qml_path = os.path.join(dirname, 'Qt', 'qml')
    engine.addImportPath(qml_path)
    qmlRegisterType(DeclarativeUAVCamera, 'UAVControl', 1, 0, 'UAVCamera')
    qmlRegisterType(Detector, 'UAVControl', 1, 0, 'Detector')
    qmlRegisterType(Engager, 'UAVControl', 1, 0, 'Engager')

    engine.load("qt_control.qml")
    app.exec_()
