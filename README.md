# Screenshot Tool

Ein Tool zum automatischen Extrahieren von hochwertigen Screenshots aus Videos, speziell für Podcasts und andere Videoproduktionen.

## Features

- **Automatische Frame-Analyse**: Findet die besten Frames basierend auf Gesichtserkennung, Schärfe und Stabilität
- **Manuelle Frame-Auswahl**: Scrubben durch das Video und manuelles Hinzufügen von Frames
- **LUT-Farbkorrektur**: Unterstützung für .cube LUT-Dateien zur Farbkorrektur
- **Verschiedene Projekttypen**: Optimierte Einstellungen für Podcast, Dokumentation, Commercial, Interview, B-Roll
- **Flexible Export-Optionen**: PNG, JPG, TIFF, WebP, BMP mit einstellbarer Qualität
- **Web-App**: Browser-basierte Version mit Chunked Upload für große Dateien (bis 10GB)

## Installation

### Voraussetzungen

- Python 3.9+
- ffmpeg (für Videoanalyse)

### Setup

```bash
# Repository klonen
git clone https://github.com/alexstoesslein/podcast-screenshot-tool.git
cd podcast-screenshot-tool

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

## Starten

### Desktop App (PyQt6)

```bash
python -m src.gui.main_window
```

### Web App (Flask)

```bash
python web/app.py
```

Dann öffne http://127.0.0.1:5001 im Browser.

### macOS App erstellen

```bash
python build_app.py
```

Die App wird im Projektordner erstellt und kann auf den Desktop oder in den Applications-Ordner verschoben werden.

## Verwendung

1. **Video importieren**: Klicke auf "Video importieren" und wähle eine Videodatei
2. **Projekttyp wählen**: Wähle den passenden Projekttyp für optimierte Analyse-Gewichtungen
3. **Analysieren**: Klicke auf "Video analysieren" um automatisch die besten Frames zu finden
4. **Manuell hinzufügen**: Alternativ kannst du durch das Video scrubben und Frames manuell hinzufügen
5. **LUT anwenden** (optional): Lade eine .cube LUT-Datei für Farbkorrektur
6. **Exportieren**: Wähle Format, Qualität und Speicherort, dann klicke auf "Screenshots exportieren"

## Tastenkürzel

- `←` / `→`: Frame vor/zurück
- `Leertaste`: Aktuelles Frame zur Auswahl hinzufügen

## Technologie

- Python 3 + PyQt6 für die GUI
- OpenCV für Videoanalyse und Bildverarbeitung
- Haar Cascades für Gesichtserkennung
- NumPy für effiziente Bildoperationen

## Lizenz

MIT License
