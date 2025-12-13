# Troubleshooting Guide

## 🐛 Häufige Probleme und Lösungen

### Problem: Bot empfängt keine Twitch-Nachrichten

**Symptome:**
- Bot startet ohne Fehler
- Keine Reaktion auf `!sr` Commands im Chat

**Lösungen:**

1. **Token überprüfen:**
   - Token muss mit `oauth:` beginnen (wird automatisch hinzugefügt)
   - Token muss von einem Account mit Chat-Rechten sein
   - Neuen Token generieren: https://dev.twitch.tv/console/apps
   
2. **Kanal-Name prüfen:**
   - Muss EXAKT dem Twitch-Namen entsprechen
   - Nur Kleinbuchstaben verwenden
   - Keine Leerzeichen
   
3. **Logs prüfen:**
   ```
   logs/bot.log
   ```
   Suche nach:
   - "Twitch bot connected as..." → Erfolgreich verbunden
   - Fehlermeldungen mit "Twitch"

4. **Test im Chat:**
   ```
   !sr test
   ```
   - Prüfe ob Bot online ist in der Zuschauerliste
   - Bot-Account muss im Kanal sein

### Problem: Fallback/Autopilot spielt nicht

**Symptome:**
- Queue ist leer
- Nichts wird abgespielt
- Playlist ist konfiguriert

**Lösungen:**

1. **Playlist-Rechte prüfen:**
   - Playlist MUSS "Öffentlich" sein
   - In Spotify → Playlist → ⋯ → "Als öffentlich teilen"
   
2. **Playlist-ID prüfen:**
   - Link: `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
   - ID ist: `37i9dQZF1DXcBWIGoYBM5M`
   - Wird automatisch extrahiert beim Speichern
   
3. **Spotify muss laufen:**
   - Premium Account erforderlich
   - Spotify App muss offen sein
   - Ein Gerät muss aktiv sein
   
4. **Logs prüfen:**
   ```
   logs/bot.log
   ```
   Suche nach:
   - "Queue empty and nothing playing - starting fallback"
   - "Playing fallback track: ..."
   - "Autopilot error" → Playlist-Problem

### Problem: Bot startet nicht

**Symptome:**
- Fehlermeldung beim Klicken auf "STARTEN"
- Sofortiger Absturz

**Lösungen:**

1. **Spotify-Credentials prüfen:**
   - Client ID und Secret korrekt?
   - App in https://developer.spotify.com/dashboard/ erstellt?
   - Redirect URI: `http://127.0.0.1:8888/callback` hinzugefügt?
   
2. **Dependencies installiert?**
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Python Version:**
   - Mindestens Python 3.9
   ```bash
   python --version
   ```

### Problem: Songs werden nicht gespielt

**Symptome:**
- Song wird zur Queue hinzugefügt
- Aber nichts passiert in Spotify

**Lösungen:**

1. **Spotify Premium:**
   - MUSS Premium Account sein
   - Free Account funktioniert NICHT
   
2. **Gerät aktiv:**
   - Spotify muss auf einem Gerät laufen
   - Handy, PC, Browser - egal, aber muss aktiv sein
   - Im Bot unten rechts prüfen ob Device erkannt wurde
   
3. **Playback starten:**
   - Einmal manuell Play drücken in Spotify
   - Dann "Force Play" im Bot klicken
   
4. **Device-ID prüfen:**
   ```
   logs/bot.log
   ```
   Suche nach: "Using device: ..."

## 🔍 Debug-Tipps

### Logs aktivieren

Logs sind standardmäßig aktiv in:
```
logs/bot.log
```

Für mehr Details, Level in `app.py` ändern:
```python
setup_logging(
    log_file=log_dir / "bot.log",
    level=logging.DEBUG  # Statt INFO
)
```

### Chat-Test

1. Als Bot-Account einloggen
2. In eigenen Kanal gehen
3. `!sr test` schreiben
4. In Bot-Logs prüfen ob Nachricht ankommt

### Spotify-Test

1. Spotify öffnen
2. Beliebigen Song spielen
3. Bot starten
4. In Logs prüfen: "Using device: ..."
5. Wenn kein Device → Spotify neu starten

## 📋 Checkliste vor Start

- [ ] Python 3.9+ installiert
- [ ] Dependencies installiert (`pip install -r requirements.txt`)
- [ ] Spotify Premium Account
- [ ] Spotify App läuft auf einem Gerät
- [ ] Spotify Developer App erstellt
- [ ] Client ID & Secret kopiert
- [ ] Redirect URI eingetragen: `http://127.0.0.1:8888/callback`
- [ ] Twitch Token generiert
- [ ] Kanal-Name korrekt (kleingeschrieben)
- [ ] (Optional) Öffentliche Playlist für Autopilot

## 🆘 Immer noch Probleme?

1. **Logs prüfen:**
   ```
   logs/bot.log
   ```
   
2. **Console Output:**
   Starte Bot im Terminal:
   ```bash
   python app.py
   ```
   Fehler werden in Console angezeigt
   
3. **Config neu erstellen:**
   - `config_premium.json` löschen
   - Bot neu starten
   - Alle Einstellungen neu eingeben
   
4. **Neuinstallation:**
   ```bash
   # Virtual env löschen
   rm -rf venv
   
   # Neu erstellen
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

## 🔧 Erweiterte Diagnostik

### Event Loop Check

In `src/ui/main_window.py` nach diesem Log suchen:
```
GUI initialized
```

Wenn nicht vorhanden → Event Loop Problem

### Twitch Connection

In Logs nach:
```
Twitch bot connected as <botname> to <channel>
```

Wenn nicht vorhanden:
- Token falsch
- Kanal existiert nicht
- Netzwerk-Problem

### Spotify Connection

In Logs nach:
```
Successfully connected to Spotify
```

Wenn nicht vorhanden:
- Credentials falsch
- Spotify API down
- Netzwerk-Problem

---

**Wenn nichts hilft:** Issue auf GitHub erstellen mit:
- `logs/bot.log` Inhalt
- Python Version
- OS (Windows/Mac/Linux)
- Genaue Fehlerbeschreibung
