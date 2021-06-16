import QtQuick 2.2
import QtQuick.Window 2.2
import QtMultimedia 5.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import UAVControl 1.0

Window {
    UAVCamera {
        id: uavCamera
    }

    VideoOutput {
        id: video
        source: uavCamera

        height: parent.height
        width: (parent.height / 3) * 4
    }

    Item {
        anchors.left: video.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Button {
            text: 'Взлёт'
            onClicked: uavCamera.arm()
            visible: uavCamera != null && uavCamera.state == UAVCamera.Disarmed
            anchors.centerIn: parent
        }

        Text {
            text: 'Взлёт...'
            visible: uavCamera != null && uavCamera.state == UAVCamera.Arming
            anchors.margins: parent.width / 50
            fontSizeMode: Text.Fit
            anchors.centerIn: parent
            font.pointSize: 50
        }

        Text {
            text: 'Посадка...'
            visible: uavCamera != null && uavCamera.state == UAVCamera.Disarming
            anchors.margins: parent.width / 50
            fontSizeMode: Text.Fit
            anchors.centerIn: parent
            font.pointSize: 50
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: parent.width / 50
            spacing: parent.width / 50
            visible: uavCamera != null && uavCamera.state == UAVCamera.Armed

            Switch {
                text: 'Режим слежения'
            }

            Item {
                Layout.fillHeight: true
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