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
├── app/            # Einstiegspunkt, Konfiguration, Zustand, Orchestrator (Assistant)
├── ai/             # Claude-Anbindung, Conversation Manager, Systemprompt
├── voice/          # Mikrofon, Wake Word, Speech-to-Text, Text-to-Speech
├── tools/          # Tool-System (System, Anwendungen, Dateien, Web, Kommunikation, Rechner)
├── security/       # Sicherheits-/Bestätigungsmechanismus für gefährliche Aktionen
├── ui/             # PySide6-GUI (Chat, Zustandsanzeige, Mikrofon-Umschalter)
└── tests/          # pytest-Suite (alle externen APIs gemockt)
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

Im GUI-Modus zeigt der Zustand (IDLE / LISTENING / THINKING / SPEAKING / ERROR)
oben farblich an, was JARVIS gerade tut. Der Mikrofon-Button startet:

- bei aktivem Wake Word (`WAKE_WORD_ENABLED=true`): dauerhaftes Zuhören auf
  das Aktivierungswort ("Jarvis"), danach eine Aufnahme pro Erkennung
- bei deaktiviertem Wake Word: eine einzelne Aufnahme pro Klick (Push-to-Talk)

Texteingaben werden nicht automatisch vorgelesen (reiner Chat); Anfragen über
das Mikrofon werden immer sowohl als Text angezeigt als auch gesprochen
beantwortet.

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
oder Display entwickelt. Die komplette Logik (Konfiguration, Conversation
Manager, Claude-Anbindung, Tool-System, Sicherheitsabfragen, STT/TTS-Fabriken,
Wake-Word-Logik) ist durch die pytest-Suite mit gemockten Abhängigkeiten
abgedeckt. Ein echter End-to-End-Test mit Mikrofon, Lautsprecher und
sichtbarer GUI sollte auf einem Windows-Rechner erfolgen.

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
