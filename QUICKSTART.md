# Quick Start Guide

## 🚀 Schnellstart

### 1. Installation

```bash
# Dependencies installieren
pip install -r requirements.txt
```

### 2. Erste Konfiguration

1. Starte den Bot:

   ```bash
   python app.py
   ```

2. Klicke auf "Einstellungen ⚙️"

3. Erforderliche Einstellungen:

   **Twitch:**
   - Kanal: `dein_twitch_name` (kleingeschrieben!)
   - Token: Hole dir einen auf <https://twitchapps.com/tmi/>

   **Spotify:**
   - Client ID & Secret: Erstelle eine App auf <https://developer.spotify.com/dashboard/>
   - Redirect URI in Spotify App: `http://127.0.0.1:8888/callback`

   **Optional - Autopilot:**
   - Erstelle eine Spotify Playlist
   - Setze sie auf "Öffentlich"
   - Kopiere den Link und füge ihn ein

4. Klicke "SPEICHERN & PRÜFEN"

### 3. Bot starten

1. Klicke "STARTEN"
2. Beim ersten Start: Autorisiere Spotify im Browser
3. ✅ Bot ist online!

## 💬 Chat Commands

```text
!sr Songname             # Song suchen
!sr Spotify-Link         # Direkter Link
```

## 🎛️ GUI Bedienung

- **Smart Voting**: Aktiviert automatische Sortierung nach Votes
- **▲/▼**: Song in Queue verschieben
- **📌**: Song fixieren (manuell gepinnt)
- **⏭ Skip**: Aktuellen Song überspringen
- **▶ Force Play**: Nächsten Song sofort starten

## ⚡ Tipps

- Spotify muss auf einem Gerät laufen
- Premium Account erforderlich
- Bot benötigt OAuth-Autorisierung beim ersten Start
- Logs findest du im `logs/` Ordner

## 🐛 Probleme?

Siehe `README.md` → Troubleshooting

---

### Viel Erfolg! 🎵
