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

    Rectangle {
        anchors.left: video.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        ColumnLayout{
            anchors.fill: parent
            anchors.margins: parent.width / 10
            spacing: parent.width / 10

            Switch {
                text: 'Режим слежения'
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
                    }
                    Button {
                        text: 'Ниже'
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }

            GroupBox {
                title: 'Управление'
                Layout.fillWidth: true

                GridLayout {
                    columns: 3
                    anchors.fill: parent
                    Layout.alignment: Qt.AlignHCenter

                    Button {
                        text: '⟲'
                    }
                    Button {
                        text: '▲'
                    }
                    Button {
                        text: '⟳'
                    }
                    Button {
                        text: '◀'
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Button {
                        text: '▶'
                    }
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                    }
                    Button {
                        text: '▼'
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