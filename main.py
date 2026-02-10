#!/usr/bin/env python3
"""
Podcast Screenshot Tool

Ein Tool zum automatischen Extrahieren von hochwertigen Screenshots
aus Podcast-Videoaufnahmen.

Funktionen:
- Automatische Erkennung guter Frames (Gesichter, Schaerfe)
- Manuelle Frame-Auswahl
- LUT-Unterstuetzung fuer Color Grading
- Export in verschiedenen Formaten (JPG, PNG, TIFF, WebP, BMP)

Verwendung:
    python main.py

Autor: Podcast Screenshot Tool
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.gui.main_window import run_app


if __name__ == "__main__":
    run_app()
