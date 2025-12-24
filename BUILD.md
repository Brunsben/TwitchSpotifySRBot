# Build Instructions

## Voraussetzungen

1. **Python installieren** (falls noch nicht geschehen)
2. **Alle Dependencies installieren:**

```bash
pip install -r requirements.txt
```

3\. **PyInstaller installieren:**

```bash
pip install pyinstaller
```

## Build erstellen

### Einfachste Methode

```bash
pyinstaller TwitchSRBot.spec
```

**Das war's!** Die fertige `.exe` ist in `dist/TwitchSRBot.exe`

### Alternative: Manueller Befehl

```bash
pyinstaller --name=TwitchSRBot ^
    --onefile ^
    --windowed ^
    --add-data="locales;locales" ^
    --add-data="src;src" ^
    --hidden-import=customtkinter ^
    --hidden-import=twitchio ^
    --collect-all=customtkinter ^
    app.py
```

## Ergebnis

Die fertige `.exe` Datei befindet sich in:

```text
dist/TwitchSRBot.exe
```

**Größe:** Ca. 30-50 MB (das ist normal für Python GUI Apps)

Diese Datei ist **standalone** und kann ohne Python-Installation ausgeführt werden!

## Für User verteilen

1. Kopiere nur die `TwitchSRBot.exe` aus dem `dist` Ordner
2. User können die .exe einfach doppelklicken
3. Die App erstellt automatisch beim ersten Start:
   - `config_premium.json` (Einstellungen)
   - `logs/` Ordner (Log-Dateien)
   - `.cache` (Spotify Auth)

## Troubleshooting

### "pyinstaller: command not found"

```bash
python -m PyInstaller TwitchSRBot.spec
```

### Build schlägt fehl

- Stelle sicher dass alle Dependencies installiert sind
- Versuche: `pip install -r requirements.txt --upgrade`

### CustomTkinter Theme fehlt

- Das sollte durch `--collect-all=customtkinter` gelöst sein
- Falls nicht: Kopiere `customtkinter` Ordner manuell in dist

### Sehr große .exe (>100MB)

- Das ist normal! Python + GUI + alle Libraries
- Alternative: Verwende `--onedir` statt `--onefile`

  - Mehrere Dateien, aber schnellerer Start
  - Ändere in .spec: `onefile=False`
