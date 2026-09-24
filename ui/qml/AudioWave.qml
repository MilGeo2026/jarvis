import QtQuick

// Wiederverwendbare Wellenform-Anzeige, angetrieben von einem 0..1-Pegelwert
// (echter Mikrofon-Pegel beim Zuhoeren, synthetischer Sprech-Puls beim Sprechen).
Item {
    id: wave

    property real level: 0.0
    property color color: "#00BFFF"
    property int barCount: 28

    width: 260
    height: 36

    property var samples: []

    Timer {
        interval: 55
        running: true
        repeat: true
        onTriggered: {
            var arr = wave.samples.slice()
            arr.push(wave.level)
            if (arr.length > wave.barCount) {
                arr.shift()
            }
            wave.samples = arr
        }
    }

    Row {
        anchors.centerIn: parent
        spacing: 3

        Repeater {
            model: wave.barCount
            delegate: Rectangle {
                width: 3
                radius: 1.5
                color: wave.color
                height: 4 + (wave.samples[index] !== undefined ? wave.samples[index] : 0) * (wave.height - 4)
                anchors.bottom: parent.bottom
                Behavior on height {
                    NumberAnimation { duration: 90; easing.type: Easing.OutQuad }
                }
            }
        }
    }
}
