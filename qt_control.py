import os
import sys

import PySide2
from PySide2.QtCore import QObject, Property, Signal, QThread, QCoreApplication
from PySide2.QtGui import QImage
from PySide2.QtMultimedia import QMediaObject, QMediaService, QVideoRendererControl, QVideoFrame, QVideoSurfaceFormat, \
    QAbstractVideoSurface, QMediaControl
from PySide2.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide2.QtWidgets import QApplication
from control import Control
from pioneer_sdk import Pioneer


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
        super(UAVCameraService, self).__init__(None)
        self._control_wrapper: ControlWrapper = ControlWrapper()
        self._video_renderer_control = UAVRendererControl(self, self._control_wrapper.control.controller)

    def requestControl(self, name: bytes) -> QMediaControl:
        if name == "org.qt-project.qt.videorenderercontrol/5.0":
            return self._video_renderer_control
        elif name == "org.plaz.control/5.0":
            return self._control_wrapper

        return None


class UAVCamera(QMediaObject):
    def __init__(self, parent):
        super(UAVCamera, self).__init__(parent, UAVCameraService())
        self.control_wrapper = self.service().requestControl("org.plaz.control/5.0")


class DeclarativeUAVCamera(QObject):
    def __init__(self):
        super(DeclarativeUAVCamera, self).__init__()
        self._camera = UAVCamera(self)

    @Signal
    def media_object_changed(self):
        pass

    def _media_object(self):
        return self._camera

    mediaObject = Property(QObject, _media_object, notify=media_object_changed)


if __name__ == "__main__":
    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'Qt', 'plugins')
    QCoreApplication.addLibraryPath(plugin_path)

    app = QApplication(sys.argv)

    engine = QQmlApplicationEngine()
    qml_path = os.path.join(dirname, 'Qt', 'qml')
    engine.addImportPath(qml_path)
    qmlRegisterType(DeclarativeUAVCamera, 'UAVControl', 1, 0, 'UAVCamera')

    engine.load("qt_control.qml")
    app.exec_()
