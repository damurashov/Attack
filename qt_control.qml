import QtQuick 2.2
import QtQuick.Window 2.2
import QtMultimedia 5.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import UAVControl 1.0

Window {
    property bool engage: false

    id: mainWindow

    function resetRects() {
        for (var i = 0; i < rectHolder.count; ++i) {
            rectHolder.itemAt(i).visible = false;
        }
    }

    function updateRect(rect, ri) {
        var xr = video.width / video.sourceRect.width;
        var yr = video.height / video.sourceRect.height;

        rect.x = video.x + ri.x * xr;
        rect.y = video.y + ri.y * yr;
        rect.width = ri.width * xr;
        rect.height = ri.height * yr;
    }

    onEngageChanged: resetRects()

    UAVCamera {
        id: uavCamera
    }

    Detector {
        id: detector

        onFinished: {
            var r = e.rects();
            for (var i = 0; i < rectHolder.count; ++i) {
                var rect = rectHolder.itemAt(i);

                if (i < r.length) {
                    updateRect(rect, r[i])
                    rect.rectangle = r[i]
                }

                rect.visible = i < r.length
            }
        }
    }

    Engager {
        id: engager

        onFinished: {
            var r = e.rects();
            for (var i = 0; i < r.length; ++i) {
                updateRect(engageRect, r[i])
            }
        }

        onLost: {
            mainWindow.engage = false
        }
    }

    VideoOutput {
        id: video
        source: uavCamera
        filters: trackSwitch != null && trackSwitch.checked ? (mainWindow.engage ? [engager] : [detector]) : []

        height: parent.height
        width: (parent.height / 3) * 4
    }

    Repeater {
        id: rectHolder
        model: 20
        Rectangle {
            property rect rectangle: null
            color: "transparent"
            border.width: 4
            border.color: "red"
            visible: false

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    engager.rect = parent.rectangle
                    mainWindow.engage = true
                }
            }
        }
    }

    Rectangle {
        id: engageRect
        color: "transparent"
        border.color: "lawngreen"
        border.width: 4
        visible: mainWindow.engage
    }

    Button {
        text: 'Выход'
        onClicked: mainWindow.close()
    }

    Item {
        anchors.left: video.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom



        ColumnLayout {
            anchors.fill: parent
            anchors.margins: parent.width / 50
            spacing: parent.width / 50
            visible: uavCamera != null

            Switch {
                id: trackSwitch
                text: 'Режим слежения'
                onCheckedChanged: {
                    mainWindow.engage = false
                }
            }

            Switch {
                text: 'Атака'
                onCheckedChanged: {
                    uavCamera.attack(this.checked)
                }
            }

            Button {
                text: 'Сброс'
                Layout.alignment: Qt.AlignHCenter
                visible: mainWindow.engage
                onClicked: {
                    mainWindow.engage = false
                }
            }

            Item {
                Layout.fillHeight: true
            }

            Button {
                text: 'Взлёт'
                onClicked: uavCamera.arm()
                visible: uavCamera != null
                anchors.centerIn: parent
            }

            Button {
                text: 'Посадка'
                Layout.alignment: Qt.AlignHCenter
                onClicked: uavCamera.disarm()
            }

            Item {
                Layout.fillHeight: true
            }

            GroupBox {
                title: 'Высота'
                Layout.fillWidth: true

                RowLayout {
                    anchors.fill: parent
                    Button {
                        text: 'Выше'
                        Layout.alignment: Qt.AlignHCenter
                        onPressed: uavCamera.setThrottle(1.0)
                        onReleased: uavCamera.setThrottle(0.0)
                    }

                    Button {
                        text: 'Ниже'
                        Layout.alignment: Qt.AlignHCenter
                        onPressed: uavCamera.setThrottle(-1.0)
                        onReleased: uavCamera.setThrottle(0.0)
                    }
                }
            }

            GroupBox {
                title: 'Управление'
                Layout.fillWidth: true

                GridLayout {
                    columns: 3
                    anchors.fill: parent

                    Button {
                        text: '⟲'
                        Layout.alignment: Qt.AlignHCenter
                        Layout.minimumWidth: Layout.minimumHeight
                        onPressed: uavCamera.setYaw(-1.0)
                        onReleased: uavCamera.setYaw(0.0)
                    }
                    Button {
                        text: '▲'
                        Layout.alignment: Qt.AlignHCenter
                        Layout.minimumWidth: Layout.minimumHeight
                        onPressed: uavCamera.setPitch(1.0)
                        onReleased: uavCamera.setPitch(0.0)
                    }
                    Button {
                        text: '⟳'
                        Layout.alignment: Qt.AlignHCenter
                        Layout.minimumWidth: Layout.minimumHeight
                        onPressed: uavCamera.setYaw(1.0)
                        onReleased: uavCamera.setYaw(0.0)
                    }
                    Button {
                        text: '◀'
                        Layout.alignment: Qt.AlignHCenter
                        Layout.minimumWidth: Layout.minimumHeight
                        onPressed: uavCamera.setRoll(-1.0)
                        onReleased: uavCamera.setRoll(0.0)
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Button {
                        text: '▶'
                        Layout.alignment: Qt.AlignHCenter
                        Layout.minimumWidth: Layout.minimumHeight
                        onPressed: uavCamera.setRoll(1.0)
                        onReleased: uavCamera.setRoll(0.0)
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Button {
                        text: '▼'
                        Layout.alignment: Qt.AlignHCenter
                        Layout.minimumWidth: Layout.minimumHeight
                        onPressed: uavCamera.setPitch(-1.0)
                        onReleased: uavCamera.setPitch(0.0)
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                }
            }
        }
    }

    width : Screen.height > Screen.width ? Screen.height : Screen.width
    height : Screen.height > Screen.width ? Screen.width : Screen.height

    visible: true
    visibility: Window.FullScreen
}