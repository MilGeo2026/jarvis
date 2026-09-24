import QtQuick

// Zeigt den aktuellen Zustand und einen kurzen Aktivitaetstext (erkannte Sprache,
// Aktionsbeschreibung, gesprochene Antwort) mit weichem Ein-/Ausblenden.
Column {
    id: panel

    property string stateText: "STANDBY"
    property string activityText: ""
    property color accentColor: "#00BFFF"
    property string fontFamily: "Consolas"

    spacing: 10
    width: 460

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: panel.stateText
        color: panel.accentColor
        font.family: panel.fontFamily
        font.pixelSize: 20
        font.letterSpacing: 6
        opacity: 0.9
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        text: panel.activityText
        color: "#CFEFFF"
        font.family: panel.fontFamily
        font.pixelSize: 13
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        width: panel.width
        opacity: panel.activityText.length > 0 ? 0.85 : 0

        Behavior on opacity {
            NumberAnimation { duration: 250 }
        }
    }
}
