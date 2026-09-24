import QtQuick
import QtQuick.Particles
import QtQuick.Effects

// Der animierte KI-Kern. Die Animation wird ausschliesslich von echten Werten
// gesteuert (assistantState, micLevel) - kein von der Logik unabhaengiges Fake-Playback.
Item {
    id: root

    property string assistantState: "STANDBY"
    property real micLevel: 0.0
    property color primaryColor: "#00BFFF"
    property color secondaryColor: "#0088AA"
    property color errorColor: "#FF4B4B"
    property bool glowEnabled: true
    property bool animationsEnabled: true
    property string fontFamily: "Consolas"

    width: 300
    height: 300

    readonly property color activeColor: assistantState === "ERROR" ? errorColor : primaryColor

    // Synthetischer Sprech-Puls: JARVIS-TTS liefert keine Amplitude, daher wird
    // hier nur waehrend SPEAKING eine plausible, weiche Wellenbewegung erzeugt.
    property real speakPhase: 0.0
    Timer {
        interval: 40
        running: root.assistantState === "SPEAKING" && root.animationsEnabled
        repeat: true
        onTriggered: root.speakPhase += 0.16
    }

    property real dynamicLevel: {
        if (assistantState === "LISTENING") return root.micLevel
        if (assistantState === "SPEAKING") return 0.35 + 0.35 * Math.abs(Math.sin(root.speakPhase))
        if (assistantState === "EXECUTING") return 0.55
        if (assistantState === "THINKING") return 0.32
        if (assistantState === "ERROR") return 0.4
        return 0.15
    }
    Behavior on dynamicLevel {
        enabled: root.animationsEnabled
        NumberAnimation { duration: 180; easing.type: Easing.OutQuad }
    }

    property real idlePulse: 0
    SequentialAnimation on idlePulse {
        running: root.animationsEnabled
        loops: Animation.Infinite
        NumberAnimation { from: 0; to: 1; duration: 3600; easing.type: Easing.InOutSine }
        NumberAnimation { from: 1; to: 0; duration: 3600; easing.type: Easing.InOutSine }
    }

    // -- Dezente Ambient-Partikel --
    ParticleSystem {
        id: particleSystem
        anchors.fill: parent
        running: root.animationsEnabled
    }
    Emitter {
        system: particleSystem
        anchors.fill: parent
        emitRate: (root.assistantState === "LISTENING" || root.assistantState === "EXECUTING") ? 7 : 2
        lifeSpan: 2600
        lifeSpanVariation: 700
        size: 4
        sizeVariation: 2
        shape: EllipseShape { fill: false }
        velocity: AngleDirection { angle: 270; angleVariation: 45; magnitude: 16; magnitudeVariation: 10 }
    }
    ItemParticle {
        system: particleSystem
        delegate: Rectangle {
            width: 3; height: 3; radius: 1.5
            color: root.activeColor
            opacity: 0.55
        }
    }

    // -- Glow --
    Rectangle {
        id: glowSource
        anchors.centerIn: parent
        width: 150 + dynamicLevel * 50 + idlePulse * 8
        height: width
        radius: width / 2
        color: root.activeColor
        opacity: 0.4 + dynamicLevel * 0.25
        visible: root.glowEnabled
    }
    MultiEffect {
        anchors.fill: glowSource
        source: glowSource
        visible: root.glowEnabled
        blurEnabled: true
        blur: 1.0
        blurMax: 48
        brightness: 0.05
    }

    // -- Rotierende HUD-Ringe --
    Canvas {
        id: ringCanvas
        anchors.fill: parent
        property real angle: 0
        RotationAnimation on angle {
            running: root.animationsEnabled
            from: 0
            to: 360
            duration: root.assistantState === "THINKING" ? 3200
                : root.assistantState === "EXECUTING" ? 900
                : root.assistantState === "LISTENING" ? 6000
                : 14000
            loops: Animation.Infinite
        }
        onAngleChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.save()
            ctx.translate(width / 2, height / 2)
            ctx.rotate(angle * Math.PI / 180)
            ctx.lineWidth = 1.4
            ctx.strokeStyle = root.activeColor
            ctx.globalAlpha = 0.55

            var r1 = Math.min(width, height) / 2 - 18
            ctx.beginPath()
            ctx.arc(0, 0, r1, 0, Math.PI * 1.3)
            ctx.stroke()

            ctx.globalAlpha = 0.35
            var r2 = r1 - 18
            ctx.beginPath()
            ctx.arc(0, 0, r2, Math.PI * 0.4, Math.PI * 1.9)
            ctx.stroke()
            ctx.restore()
        }
    }

    // -- Dot-Kranz (Motiv aus dem HUD-Mockup) --
    Repeater {
        model: 8
        delegate: Rectangle {
            property real angle: (index / 8) * 2 * Math.PI + ringCanvas.angle * Math.PI / 180 * 0.25
            width: 5; height: 5; radius: 2.5
            color: root.activeColor
            opacity: 0.5 + 0.3 * Math.sin(angle * 2)
            x: root.width / 2 + Math.cos(angle) * (68 + dynamicLevel * 12) - width / 2
            y: root.height / 2 + Math.sin(angle) * (68 + dynamicLevel * 12) - height / 2
        }
    }

    Text {
        anchors.centerIn: parent
        text: "JARVIS"
        color: root.activeColor
        font.family: root.fontFamily
        font.pixelSize: 14
        font.letterSpacing: 4
        opacity: 0.85
    }
}
