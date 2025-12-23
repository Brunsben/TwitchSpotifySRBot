# 🎵 Twitch SR Bot - Installation & Setup

## ⚡ Quick Start (für User)

### Download & Start
1. Lade `TwitchSRBot.exe` herunter
2. Doppelklick auf die `.exe` Datei
3. Fertig! 🎉

Keine Installation erforderlich - die App läuft direkt!

---

## ⚙️ Erste Einrichtung

### 1. Twitch Setup
1. Klicke auf **"Einstellungen"** in der App
2. Gehe zum Tab **"Twitch Login"**
3. Klicke auf **"🔧 Twitch App erstellen"**
   - Erstelle eine neue App in der Twitch Developer Console
   - Kopiere Client ID und Client Secret
4. Klicke auf **"🔑 Token generieren"**
   - Der Bot öffnet automatisch ein Login-Fenster
   - Melde dich mit deinem Bot-Account an
   - Token wird automatisch übernommen

### 2. Spotify Setup
1. Gehe zum Tab **"Spotify API"**
2. Erstelle eine App auf [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
3. Trage Client ID und Secret ein
4. Optional: Trage eine Autopilot Playlist ein (für Fallback-Musik)

### 3. Regeln anpassen
1. Gehe zum Tab **"Regeln & Limits"**
2. Wähle die Sprache
3. Stelle ein, wer Songs wünschen darf:
   - **Alle** - Jeder Viewer
   - **Nur Follower** - Nur deine Follower
   - **Nur Subscribers** - Nur Subs/VIPs
4. Passe Queue-Limits an

### 4. Bot starten
1. Klicke auf **"STARTEN"**
2. Der Bot verbindet sich mit Twitch und Spotify
3. Status wird auf **"ONLINE"** gesetzt

---

## 🎮 Chat Commands

### Für Viewer
- `!sr <Song oder Link>` - Song zur Queue hinzufügen
  - Beispiel: `!sr Despacito`
  - Beispiel: `!sr https://open.spotify.com/track/...`

### Für Streamer (via GUI)
- **Force Play** - Nächsten Song sofort abspielen
- **Skip** - Aktuellen Song überspringen
- **Clear All** - Komplette Queue leeren

---

## 📁 Dateien & Ordner

Die App erstellt automatisch:
- `config_premium.json` - Deine Einstellungen
- `logs/` - Log-Dateien für Debugging
- `.cache` - Spotify Authentifizierung

**Wichtig:** Behalte `config_premium.json` - dort sind alle deine Einstellungen gespeichert!

---

## 🐛 Probleme?

### Bot startet nicht
- Prüfe ob Windows Defender die `.exe` blockiert
- Rechtsklick → "Trotzdem ausführen"

### Bot empfängt keine Chat-Nachrichten
- Prüfe ob der Token gültig ist (Token neu generieren)
- Stelle sicher dass der richtige Kanalname eingetragen ist

### Songs werden nicht abgespielt
- Öffne Spotify auf einem Gerät (Desktop/Handy)
- Der Bot braucht ein aktives Spotify-Gerät

### Debug-Log aktivieren
- Klicke auf **"🔍 Debug Log"** in der Sidebar
- Kopiere Fehler aus dem Log
- Erstelle ein GitHub Issue mit dem Fehler

---

## 🔄 Updates

Für neue Versionen:
1. Lade die neue `TwitchSRBot.exe` herunter
2. Ersetze die alte Datei
3. Deine Einstellungen bleiben erhalten! ✅

---

## 💡 Tipps

- **Smart Voting aktivieren**: Songs mit mehreren Votes rutschen nach vorne
- **Autopilot Playlist**: Verhindert Stille wenn die Queue leer ist
- **Max Song Length**: Verhindert 1-Stunden-Trolls
- **Cooldown**: Songs können nicht direkt hintereinander gewünscht werden

---

## 🆘 Support

Bei Fragen oder Problemen:
- GitHub Issues: [Link zum Repo]

---

**Viel Spaß mit deinem Musik-Bot! 🎵**
