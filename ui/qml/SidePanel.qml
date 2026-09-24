import QtQuick

// Dezentes Info-Panel am Bildschirmrand (SYSTEM- oder JARVIS-Status).
// Bewusst klein und unauffaellig - der Kern bleibt das wichtigste Element.
Column {
    id: panel

    property string title: "SYSTEM"
    property var rows: []
    property color accentColor: "#00BFFF"
    property string fontFamily: "Consolas"

    spacing: 7
    width: 180

    Text {
        text: panel.title
        color: panel.accentColor
        font.family: panel.fontFamily
        font.pixelSize: 12
        font.letterSpacing: 3
        opacity: 0.75
    }

    Rectangle {
        width: 28
        height: 1
        color: panel.accentColor
        opacity: 0.4
    }

    Repeater {
        model: panel.rows
        delegate: Row {
            spacing: 10
            Text {
                text: modelData.label
                color: "#8FB6C9"
                font.family: panel.fontFamily
                font.pixelSize: 11
                width: 82
            }
            Text {
                text: modelData.value
                color: "#E4F6FF"
                font.family: panel.fontFamily
                font.pixelSize: 11
            }
        }
    }
}
