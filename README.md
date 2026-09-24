# JARVIS – persönlicher Sprachassistent

JARVIS ist ein lokal laufender, deutschsprachiger Sprachassistent auf Basis von
Claude (Anthropic). Er versteht gesprochene und getippte Anfragen, führt darauf
abgestimmte Aktionen über ein Tool-System aus, fragt vor riskanten Aktionen
aktiv nach und liest seine Antworten vor.

```
Mikrofon → Wake Word → Speech-to-Text → Claude (+ Tools) → Text-to-Speech → Lautsprecher
```

## Architektur

```
jarvis/
├── app/            # Einstiegspunkt, Konfiguration, Zustand/Events, Orchestrator (Assistant)
├── ai/             # Claude-Anbindung, Conversation Manager, Systemprompt
├── voice/          # Mikrofon, Wake Word, Speech-to-Text, Text-to-Speech, Voice-Pipeline
├── tools/          # Tool-System (System, Anwendungen, Dateien, Web, Kommunikation, Rechner)
├── security/       # Sicherheits-/Bestätigungsmechanismus für gefährliche Aktionen
├── ui/             # Futuristisches QML-HUD + Bridge/Fenster/Hotkey/Sound/Theme (PySide6)
│   └── qml/        # JarvisCore, StatusPanel, SidePanel, AudioWave, BootSequence, Main.qml
├── config/         # theme.json (Farben/Transparenz/Animation, zur Laufzeit ladbar)
└── tests/          # pytest-Suite (alle externen APIs/Qt-Backends gemockt)
```

Die `Assistant`-Klasse (`app/orchestrator.py`) ist der zentrale Knotenpunkt:
Sie schickt Nachrichten an Claude, führt angeforderte Tools aus, stellt bei
gefährlichen Aktionen eine Rückfrage zurück und führt sie erst nach
Bestätigung wirklich aus. GUI und Sprach-Pipeline rufen beide dieselbe
`Assistant.handle_text()`-Methode auf – Text- und Sprachmodus teilen sich
also die komplette Logik.

## Voraussetzungen

- Windows 10/11 (Zielplattform für Mikrofon/Lautsprecher-Zugriff)
- Python 3.11 oder neuer
- Ein Anthropic-API-Key (https://console.anthropic.com/)

## Installation (Windows / PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env   # ANTHROPIC_API_KEY eintragen
```

## Start

```powershell
# GUI mit Sprachsteuerung (Standard)
python -m app.main

# Reiner Text-Chat im Terminal (kein Mikrofon/GUI nötig)
python -m app.main --mode text
```

Der GUI-Modus startet ein rahmenloses, HUD-artiges Fenster mit animiertem
KI-Kern in der Mitte (siehe nächster Abschnitt) statt einer klassischen
Chat-Oberfläche. Es gibt bewusst keinen Mikrofon-Button:

- bei aktivem Wake Word (`WAKE_WORD_ENABLED=true`, Standard): JARVIS hört ab
  dem Start automatisch im Hintergrund auf "Jarvis" und reagiert sofort,
  ganz ohne Klick.
- bei deaktiviertem Wake Word: Sprache ist dann nicht automatisch aktiv;
  die Texteingabe am unteren Bildschirmrand ist der sekundäre Kanal
  (Tastatur/Maus, wie in Abschnitt "Minimaler Bedienmodus" vorgesehen).

`STRG + LEERTASTE` (konfigurierbar über `HOTKEY_TOGGLE`) blendet das
JARVIS-Fenster jederzeit systemweit ein/aus, auch wenn es nicht fokussiert ist.

Texteingaben werden nur angezeigt, nicht vorgelesen. Anfragen über das
Mikrofon werden immer sowohl als Text angezeigt als auch gesprochen
beantwortet.

## Futuristische HUD-Oberfläche

Die Oberfläche ist komplett in QML (Qt Quick, GPU-kompositiert) gebaut, nicht
als klassisches Widget-Fenster:

- **Zentraler KI-Kern** (`ui/qml/JarvisCore.qml`): pulsiert im Standby dezent,
  reagiert beim Zuhören in Echtzeit auf die tatsächliche Mikrofonlautstärke,
  zeigt rotierende Ringe beim Denken, eine schnelle Animation beim Ausführen
  von Tools und einen weichen Puls beim Sprechen. Die Animation liest dafür
  ausschließlich echte Werte aus `app/state.py` (`AssistantState`) und
  `app/events.py` (`AudioLevelBus`) – es gibt kein von der Logik unabhängiges
  Fake-Playback.
- **Statusanzeige** (`StatusPanel.qml`): zeigt den aktuellen Zustand
  (STANDBY/LISTENING/THINKING/EXECUTING/SPEAKING/ERROR) sowie erkannte
  Sprache, laufende Aktion oder gesprochene Antwort.
- **Seiten-Panels** (`SidePanel.qml`): dezente SYSTEM- (CPU/RAM/GPU/Netzwerk,
  `ui/system_monitor.py`, pollt alle 2 s) und JARVIS-Statuswerte am Rand.
- **Boot-Sequenz** (`BootSequence.qml`): erscheint nur beim Start, zeigt den
  echten Initialisierungsstatus (Voice/AI/Mikrofon/Tools), keine Fake-Werte.
- **Fenstermodi** (`ui/window_controller.py`, `WINDOW_MODE`): `normal`,
  `borderless` (Standard), `fullscreen` oder `overlay` (transparent,
  immer im Vordergrund über anderen Fenstern). In allen Modi außer `normal`
  lässt sich das Fenster per Ziehen mit der Maus verschieben (keine
  Titelleiste).
- **Sounds** (`ui/sound.py`): kurze Signaltöne beim Start, bei Wake-Word-
  Erkennung und beim Start einer Aktion, über `SOUND_ENABLED=false`
  abschaltbar. Nutzt `winsound` (Windows-Bordmittel, keine Zusatzdateien).
- **Theme** (`config/theme.json`): Primär-/Sekundärfarbe, Fehlerfarbe,
  Hintergrund-Transparenz, Schriftart, Glow/Animationen an/aus – zentral an
  einer Stelle änderbar, ohne Code anzufassen.

## Konfiguration (`.env`)

| Variable | Bedeutung | Standard |
|---|---|---|
| `ANTHROPIC_API_KEY` | Erforderlich für Claude | – |
| `ANTHROPIC_MODEL` | Claude-Modell | `claude-sonnet-5` |
| `LANGUAGE` | Sprache für STT/Antworten | `de` |
| `STT_PROVIDER` | `local` (faster-whisper, kostenlos/offline) oder `cloud` (OpenAI Whisper API) | `local` |
| `STT_LOCAL_MODEL` | Whisper-Modellgröße (`tiny`…`medium`) | `small` |
| `TTS_PROVIDER` | `windows` (SAPI via pyttsx3, kostenlos), `cloud` oder `custom` | `windows` |
| `TTS_VOICE` / `TTS_SPEED` | Stimme / Sprechgeschwindigkeit | – / `1.0` |
| `WAKE_WORD_ENABLED` | Aktivierungswort an/aus | `true` |
| `WAKE_WORD` | Aktivierungswort | `jarvis` |
| `LOG_LEVEL` | Logging-Level | `INFO` |
| `WINDOW_MODE` | `normal` / `borderless` / `fullscreen` / `overlay` | `borderless` |
| `ALWAYS_ON_TOP` | Fenster immer im Vordergrund | `false` |
| `HOTKEY_TOGGLE` | Globaler Hotkey zum Ein-/Ausblenden (pynput-Syntax) | `<ctrl>+<space>` |
| `SOUND_ENABLED` | Dezente UI-Sounds an/aus | `true` |
| `BOOT_SEQUENCE_ENABLED` | Boot-Sequenz beim Start anzeigen | `true` |
| `THEME_PATH` | Pfad zur Theme-JSON-Datei | `config/theme.json` |

STT/TTS sind bewusst austauschbar gehalten (`voice/speech_to_text.py`,
`voice/text_to_speech.py`): eine neue Implementierung muss nur das jeweilige
Interface erfüllen und in der `create_stt`/`create_tts`-Factory ergänzt
werden – der Rest der Anwendung ändert sich nicht.

## Sicherheitsmechanismus

Tools, die Daten überschreiben oder Anwendungen beenden können
(`close_application`, `create_file`/`move_file`/`copy_file` bei bereits
existierendem Ziel), werden als "gefährlich" eingestuft. JARVIS führt sie
nicht sofort aus, sondern fragt zuerst nach ("Soll ich … wirklich …?") und
führt die Aktion erst nach einer eindeutigen Bestätigung ("Ja"/"Nein" im
nächsten Gesprächsschritt) aus. Siehe `security/confirmation.py`.

## Tools

System: `get_system_information`, `get_current_time`, `get_current_date`
Anwendungen: `open_application`, `close_application`, `open_website`
Dateien: `search_files`, `read_file`, `create_file`, `move_file`, `copy_file`
Web: `web_search` · Kommunikation: `send_notification` · Rechner: `calculator`

Neue Tools: eine `Tool`-Unterklasse in `tools/` anlegen und in
`tools/__init__.py::build_default_registry()` registrieren.

## Tests

```powershell
pytest
```

Alle Tests mocken externe Abhängigkeiten (Anthropic-API, Mikrofon,
faster-whisper, pyttsx3, Netzwerk) und benötigen keinen echten API-Key.

## Hinweise zur Entwicklungsumgebung

Dieses Projekt wurde in einer Linux-Cloud-Umgebung ohne Mikrofon, Lautsprecher
oder echtes Display entwickelt. Die komplette Logik (Konfiguration,
Conversation Manager, Claude-Anbindung, Tool-System, Sicherheitsabfragen,
STT/TTS-Fabriken, Wake-Word-Logik, Zustands-Bridge, Fenstermodi, Hotkey,
Sound-Toggle, Theme) ist durch die pytest-Suite mit gemockten Abhängigkeiten
abgedeckt. Das QML-HUD wurde zusätzlich headless geladen (Qt "offscreen"-
Plattform + Software-Rendering) und einmal durch alle Zustände
(STANDBY→LISTENING→THINKING→EXECUTING→SPEAKING→ERROR) durchlaufen – dabei
traten keine QML-/Bindungsfehler auf. Das tatsächliche Aussehen, Timing-Gefühl
und die Performance der Animationen (Ziel: flüssig, geringe Idle-CPU-Last)
lassen sich in dieser Umgebung ohne echtes Display/GPU nicht beurteilen und
sollten auf dem Ziel-Windows-Rechner geprüft werden.

## Bekannte Grenzen / mögliche Erweiterungen

- Die Bestätigungslogik erkennt Ja/Nein anhand einfacher deutscher
  Schlüsselwörter (`security/confirmation.py::interpret_yes_no`) – für
  komplexere Freitext-Bestätigungen könnte hier später Claude selbst
  einbezogen werden.
- Das Wake Word wird per kurzem STT-Fenster erkannt (kein dedizierter,
  kostenpflichtiger Wake-Word-Dienst nötig). Für geringeren Rechenaufwand
  ließe sich später z. B. Picovoice Porcupine hinter demselben
  `WakeWordDetector`-Interface ergänzen.
- `web_search` nutzt eine kostenlose HTML-Suche ohne API-Key; für
  zuverlässigere Ergebnisse kann später eine Such-API (z. B. Brave Search)
  angebunden werden.
- Die Kern-Visualisierung reagiert beim Zuhören auf die echte
  Mikrofonlautstärke, beim Sprechen aber auf einen synthetischen Puls
  (`JarvisCore.qml::speakPhase`), da pyttsx3/SAPI keine Lautstärke-Amplitude
  der Sprachausgabe liefert. Für eine echte Audio-Reaktivität beim Sprechen
  müsste ein TTS-Provider verwendet werden, der PCM-Samples statt nur "sprich
  diesen Text" liefert.
- `AI CORE` in der Boot-Sequenz zeigt "ONLINE", sobald ein
  `ANTHROPIC_API_KEY` konfiguriert ist – ohne einen echten (kostenpflichtigen)
  Testaufruf beim Start lässt sich reale Erreichbarkeit nicht verifizieren.
- Der globale Hotkey (`pynput`) benötigt eine laufende Desktop-Sitzung mit
  Eingabe-Backend; in Umgebungen ohne Display (wie diesem Entwicklungs-
  Container) wird er automatisch und ohne Absturz deaktiviert.
- Fenstermodus, Theme und Sound werden aktuell nur beim Start aus `.env`
  bzw. `config/theme.json` gelesen; eine Laufzeit-Umschaltung über die GUI
  selbst ist nicht implementiert (Konfigurationsdatei ändern + Neustart).
