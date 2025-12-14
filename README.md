# 🎵 Twitch SR Bot

![Version](https://img.shields.io/badge/version-0.9.5-green.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![TwitchIO](https://img.shields.io/badge/TwitchIO-3.1.0-purple.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Moderner EventSub-basierter Twitch Song Request Bot mit Spotify-Integration. Zuschauer können Songs per Chat-Command wünschen, die automatisch zur Warteschlange hinzugefügt und abgespielt werden.

> **⚠️ WICHTIG:** Für die Steuerung der Spotify-Wiedergabe wird ein **Spotify Premium Account** benötigt!

## ✨ Features

- 🎤 **Song Requests**: Chat-basierte Song-Wünsche (`!sr`)
- �️ **Smart Voting**: Mehrfach gewünschte Songs steigen in der Queue auf
- �🔐 **Berechtigungssystem**: 
  - Alle User
  - Nur Follower (mit Twitch API Verifikation)
  - Nur Subscriber
- ⏱️ **Intelligente Limits**:
  - Max. Queue-Größe
  - Songs pro User
  - Song-Länge
  - Cooldown-System
- 🎯 **Queue Management**: Live-Updates, Sortierung, Force Play
- 🤖 **Autopilot**: Fallback-Playlist wenn Queue leer
- 🌍 **Multi-Language**: Deutsch & Englisch
- 🎨 **Moderne UI**: CustomTkinter mit Dark Theme
- 📊 **Live-Logs**: Ein-/ausblendbare Debug-Informationen
- 🔄 **EventSub WebSocket**: Moderne Twitch API (kein IRC)

## 🚀 Quick Start

### Option 1: Standalone Executable (Empfohlen)

1. Download `TwitchSRBot.exe` aus den [Releases](https://github.com/Brunsben/TwitchSpotifySRBot/releases)
2. Starte die `.exe` - keine Installation nötig!
3. Folge der [Installations-Anleitung](INSTALL.md)

### Option 2: Python

```bash
git clone https://github.com/Brunsben/TwitchSpotifySRBot.git
cd TwitchSpotifySRBot
pip install -r requirements.txt
python app.py
```

## 📋 Voraussetzungen

### Für Twitch
- Twitch Developer App ([dev.twitch.tv/console](https://dev.twitch.tv/console))
- OAuth Redirect URL: `http://localhost:3000`
- Scopes: `user:read:chat`, `user:write:chat`, `user:bot`

### Für Spotify
- **Spotify Premium Account** (erforderlich für Playback-Steuerung!)
- Spotify Developer App ([developer.spotify.com](https://developer.spotify.com/dashboard))
- Redirect URI: `http://localhost:8888/callback`

**Detaillierte Anleitung**: [INSTALL.md](INSTALL.md)

## 🎮 Verwendung

### Chat Commands

```
!sr <Songname>          - Sucht und fügt Song hinzu
!sr <Spotify-Link>      - Fügt Song direkt hinzu
!currentsong            - Zeigt aktuellen Song
!skip                   - Überspringt Song (nur Broadcaster/Mods)
```

**Beispiele:**
```
!sr Never Gonna Give You Up
!sr https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
```

### GUI Bedienung

- **STARTEN/STOPPEN**: Bot-Verbindung steuern
- **Force Play**: Ausgewählten Song sofort spielen
- **Skip**: Aktuellen Song überspringen
- **Alle löschen**: Queue komplett leeren
- **🔍 Debug Log**: Technische Logs anzeigen/verbergen

## 🏗️ Architektur

```
TwitchSpotifySRBot/
├── app.py                    # Einstiegspunkt
├── requirements.txt          # Dependencies
├── src/
│   ├── constants.py         # Version & Metadaten
│   ├── models/              # Datenmodelle (Pydantic)
│   │   ├── config.py       # Konfiguration
│   │   └── song.py         # Song & Queue Items
│   ├── services/            # Business Logic
│   │   ├── twitch_service.py      # TwitchIO 3.x EventSub
│   │   ├── spotify_service.py     # Spotify Web API
│   │   ├── queue_manager.py       # Queue-Logik
│   │   └── bot_orchestrator.py    # Koordination
│   ├── ui/                  # GUI (CustomTkinter)
│   │   ├── main_window.py
│   │   ├── settings_window.py
│   │   └── help_window.py
│   └── utils/               # Hilfsfunktionen
│       ├── config_manager.py
│       ├── i18n.py
│       ├── logging_config.py
│       └── twitch_oauth.py
└── locales/                 # Übersetzungen (DE/EN)
```

## 🔧 Einstellungen

### Berechtigungen
- **Alle**: Jeder kann Songs wünschen
- **Nur Follower**: Twitch API prüft Follower-Status (5 Min. Cache)
- **Nur Subscriber**: Nur Subs dürfen Requests machen

### Regeln & Limits
- **Max. Queue**: Warteschlangengröße (z.B. 10)
- **Max. pro User**: Songs gleichzeitig pro User (z.B. 2)
- **Max. Länge**: Song-Dauer in Minuten (z.B. 8)
- **Cooldown**: Minuten bis Song erneut gewünscht werden kann (z.B. 30)

### Autopilot
- **Zweck**: Spielt Musik wenn Queue leer
- **Setup**: Link zu **öffentlicher** Spotify Playlist
- Wechselt automatisch zwischen Requests und Autopilot

## 🔬 Technologie

- **Python 3.13**: Moderne Features & Performance
- **TwitchIO 3.1.0**: EventSub WebSocket API (moderne Architektur)
- **Spotipy 2.23.0**: Spotify Web API
- **CustomTkinter**: Modernes GUI Framework
- **Pydantic 2.0**: Type-Safe Konfiguration
- **PyInstaller**: Standalone Executables

### Was ist EventSub?

TwitchIO 3.x nutzt **EventSub über WebSocket** statt IRC:
- ✅ Offizielle Twitch API
- ✅ Moderne OAuth2-Authentifizierung
- ✅ Bessere Skalierbarkeit
- ✅ Echtzeit-Events
- ❌ Kein IRC mehr

## 🔨 Build von Source

```bash
# PyInstaller installieren
pip install pyinstaller

# Executable bauen
python build.py

# Output: dist/TwitchSRBot.exe
```

Details: [BUILD.md](BUILD.md)

## 🐛 Troubleshooting

### Bot empfängt keine Nachrichten
- ✅ Prüfe OAuth Scopes (`user:read:chat`, `user:write:chat`, `user:bot`)
- ✅ Erstelle neuen Token mit korrekten Scopes
- ✅ TwitchIO 3.x benötigt EventSub-Authentifizierung

### Follower-Check funktioniert nicht
- ✅ Twitch App benötigt zusätzliche Permissions
- ✅ Cache wird alle 5 Minuten aktualisiert
- ✅ Prüfe Logs für API-Fehler

### Autopilot spielt nicht
- ✅ Playlist muss **ÖFFENTLICH** sein
- ✅ Spotify muss aktiv sein (auf irgendeinem Gerät)
- ✅ Premium Account erforderlich

Weitere Hilfe: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 📝 Changelog

### v0.9.5 (2025-12-14)
- 🐛 Fixed browser window stealing focus on bot startup
- 🔧 Added global webbrowser patch to prevent focus theft
- 🔗 Fixed Help window links to use autoraise=False

### v0.9.4 (2025-12-13)
- 📖 Comprehensive Smart Voting documentation
- 📚 Added detailed help section explaining voting system
- 🎯 Updated README with Smart Voting feature

### v0.9.3 (2025-12-13)
- ✨ Added !skip command (Broadcaster/Moderator only)
- ✨ Added !currentsong / !song command (all users)
- 🔒 Browser no longer steals focus during OAuth (prevents token leaks)
- 🔗 Developer portal buttons in settings (Twitch & Spotify)
- 🎯 Username mentions in command responses

### v0.9.2 (2025-12-13)
- 🎮 Initial implementation of new chat commands
- 🐛 Bug fixes and improvements

### v0.9.1 (2025-12-13)
- 🐛 Fixed PyInstaller resource paths
- 📖 Comprehensive help documentation
- ✅ All locales load correctly in .exe

### v0.9.0 (2025-12-13)
- ✨ Complete refactor from monolithic to modular architecture
- 🔄 Migration to TwitchIO 3.x EventSub
- 🔐 Permission system (all/followers/subscribers)
- 🌐 Follower API integration with caching
- 🎨 Tab-based settings UI
- 📊 Toggle-able debug logs
- 🌍 Multi-language support
- 🏗️ Modern async architecture
- 📦 PyInstaller build system

### Legacy (Pre-v0.9.0)
- Original monolithic implementation
- TwitchIO 2.x IRC-based

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 👤 Autor

**uprisin6**  
GitHub: [@Brunsben](https://github.com/Brunsben)

## 🙏 Credits

- [TwitchIO](https://github.com/TwitchIO/TwitchIO) - EventSub WebSocket Integration
- [Spotipy](https://github.com/spotipy-dev/spotipy) - Spotify Web API
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI
- [Pydantic](https://github.com/pydantic/pydantic) - Data Validation

## 🔗 Links

- 📦 [Releases](https://github.com/Brunsben/TwitchSpotifySRBot/releases)
- 📖 [Installation Guide](INSTALL.md)
- 🔨 [Build Instructions](BUILD.md)
- 🐛 [Troubleshooting](TROUBLESHOOTING.md)
- 🔄 [Migration from Legacy](MIGRATION.md)

---

**Viel Spaß beim Streamen! 🎵**
