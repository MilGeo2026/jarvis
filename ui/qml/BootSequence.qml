import QtQuick

// Kurze Boot-Sequenz beim Start. Zeigt echte Initialisierungsergebnisse
// (Voice/AI/Mikrofon/Tools kommen aus der Bridge, sind also kein Fake-Text).
Rectangle {
    id: boot

    property bool bridgeShowBoot: true
    property color accentColor: "#00BFFF"
    property string fontFamily: "Consolas"
    property bool voiceOnline: false
    property bool aiOnline: false
    property bool micOnline: false
    property bool toolsOnline: false
    property bool systemOnline: true

    color: "#04070C"
    opacity: bridgeShowBoot ? 1 : 0
    visible: opacity > 0.01

    Behavior on opacity {
        NumberAnimation { duration: 600; easing.type: Easing.InOutQuad }
    }

    Column {
        anchors.centerIn: parent
        spacing: 16

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "INITIALIZING JARVIS..."
            color: boot.accentColor
            font.family: boot.fontFamily
            font.pixelSize: 18
            font.letterSpacing: 3
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 320
            height: 4
            radius: 2
            color: "#132430"

            Rectangle {
                width: 0
                height: parent.height
                radius: 2
                color: boot.accentColor
                NumberAnimation on width {
                    running: boot.bridgeShowBoot
                    from: 0
                    to: 320
                    duration: 1600
                    easing.type: Easing.OutCubic
                }
            }
        }

        Column {
            spacing: 6
            anchors.horizontalCenter: parent.horizontalCenter

            Repeater {
                model: [
                    { label: "VOICE SYSTEM", ready: boot.voiceOnline, delay: 300 },
                    { label: "AI CORE", ready: boot.aiOnline, delay: 550 },
                    { label: "MICROPHONE", ready: boot.micOnline, delay: 800 },
                    { label: "TOOLS", ready: boot.toolsOnline, delay: 1050 },
                    { label: "SYSTEM", ready: boot.systemOnline, delay: 1300 }
                ]
                delegate: Row {
                    spacing: 14
                    opacity: 0
                    SequentialAnimation on opacity {
                        running: boot.bridgeShowBoot
                        PauseAnimation { duration: modelData.delay }
                        NumberAnimation { from: 0; to: 1; duration: 300; easing.type: Easing.OutQuad }
                    }

                    Text {
                        text: modelData.label + " ........."
                        color: "#8FB6C9"
                        font.family: boot.fontFamily
                        font.pixelSize: 12
                        width: 180
                    }
                    Text {
                        text: modelData.ready ? "ONLINE" : "UNAVAILABLE"
                        color: modelData.ready ? boot.accentColor : "#FF4B4B"
                        font.family: boot.fontFamily
                        font.pixelSize: 12
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "JARVIS READY"
            color: boot.accentColor
            font.family: boot.fontFamily
            font.pixelSize: 14
            font.letterSpacing: 4
            opacity: 0
            SequentialAnimation on opacity {
                running: boot.bridgeShowBoot
                PauseAnimation { duration: 1650 }
                NumberAnimation { from: 0; to: 1; duration: 400 }
            }
        }
    }
}
