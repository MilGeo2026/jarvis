import QtQuick

// Root-Oberflaeche. "bridge" wird von Python via rootContext().setContextProperty
// bereitgestellt und ist die einzige Quelle der Wahrheit fuer den Zustand.
Rectangle {
    id: root
    anchors.fill: parent
    color: Qt.rgba(0.016, 0.027, 0.047, bridge.backgroundOpacity)

    // Dezentes technisches Grid im Hintergrund
    Canvas {
        anchors.fill: parent
        opacity: 0.06
        onPaint: {
            var ctx = getContext("2d")
            ctx.strokeStyle = bridge.primaryColor
            ctx.lineWidth = 1
            var step = 42
            for (var x = 0; x < width; x += step) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke()
            }
            for (var y = 0; y < height; y += step) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke()
            }
        }
    }

    // Vignette: Raender dezent abdunkeln, Fokus bleibt auf dem Kern
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#00000000" }
            GradientStop { position: 1.0; color: "#8A000000" }
        }
    }

    Text {
        anchors.top: parent.top
        anchors.topMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        text: "J A R V I S"
        color: bridge.textColor
        font.family: bridge.fontFamily
        font.pixelSize: 16
        font.letterSpacing: 8
        opacity: 0.55
    }

    JarvisCore {
        id: core
        anchors.centerIn: parent
        assistantState: bridge.state
        micLevel: bridge.micLevel
        primaryColor: bridge.primaryColor
        secondaryColor: bridge.secondaryColor
        errorColor: bridge.errorColor
        glowEnabled: bridge.glowEnabled
        animationsEnabled: bridge.animationsEnabled
        fontFamily: bridge.fontFamily
    }

    AudioWave {
        anchors.top: core.bottom
        anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        color: bridge.primaryColor
        level: bridge.state === "LISTENING" ? bridge.micLevel
             : bridge.state === "SPEAKING" ? core.dynamicLevel
             : 0.0
        opacity: (bridge.state === "LISTENING" || bridge.state === "SPEAKING") ? 0.85 : 0
        Behavior on opacity { NumberAnimation { duration: 250 } }
    }

    StatusPanel {
        anchors.top: core.bottom
        anchors.topMargin: 56
        anchors.horizontalCenter: parent.horizontalCenter
        stateText: bridge.state
        activityText: bridge.activityText
        accentColor: bridge.state === "ERROR" ? bridge.errorColor : bridge.primaryColor
        fontFamily: bridge.fontFamily
    }

    SidePanel {
        anchors.left: parent.left
        anchors.leftMargin: 32
        anchors.verticalCenter: parent.verticalCenter
        opacity: 0.7
        title: "SYSTEM"
        accentColor: bridge.primaryColor
        fontFamily: bridge.fontFamily
        rows: [
            { label: "CPU", value: Math.round(bridge.cpuPercent) + "%" },
            { label: "RAM", value: Math.round(bridge.ramPercent) + "%" },
            { label: "GPU", value: bridge.gpuPercent >= 0 ? (Math.round(bridge.gpuPercent) + "%") : "N/A" },
            { label: "NETWORK", value: bridge.networkOnline ? "ONLINE" : "OFFLINE" }
        ]
    }

    SidePanel {
        anchors.right: parent.right
        anchors.rightMargin: 32
        anchors.verticalCenter: parent.verticalCenter
        opacity: 0.7
        title: "JARVIS"
        accentColor: bridge.primaryColor
        fontFamily: bridge.fontFamily
        rows: [
            { label: "STATUS", value: bridge.state === "ERROR" ? "ERROR" : "ONLINE" },
            { label: "VOICE", value: bridge.voiceOnline ? "ACTIVE" : "OFFLINE" },
            { label: "AI", value: bridge.aiOnline ? "CONNECTED" : "OFFLINE" },
            { label: "MIC", value: bridge.micOnline ? "READY" : "N/A" }
        ]
    }

    // Sekundaere, minimalistische Texteingabe (Sprache bleibt die primaere Eingabe)
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 26
        anchors.horizontalCenter: parent.horizontalCenter
        width: 440
        height: 34
        radius: 17
        color: Qt.rgba(1, 1, 1, 0.05)
        border.color: Qt.rgba(1, 1, 1, 0.12)
        border.width: 1
        opacity: 0.8

        TextInput {
            id: inputField
            anchors.fill: parent
            anchors.margins: 12
            color: bridge.textColor
            font.family: bridge.fontFamily
            font.pixelSize: 13
            clip: true
            onAccepted: {
                bridge.submitText(text)
                text = ""
            }
        }
    }

    BootSequence {
        anchors.fill: parent
        bridgeShowBoot: bridge.showBoot
        accentColor: bridge.primaryColor
        fontFamily: bridge.fontFamily
        voiceOnline: bridge.voiceOnline
        aiOnline: bridge.aiOnline
        micOnline: bridge.micOnline
        toolsOnline: bridge.toolsOnline
        systemOnline: bridge.systemOnline
    }
}
