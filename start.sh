#!/bin/bash
# Podcast Screenshot Tool Starter
# Aktiviert das virtuelle Environment und startet das Tool

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Aktiviere venv und starte
source venv/bin/activate
python main.py
