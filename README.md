# Twitch Spotify Bot 🎵

![Version](https://img.shields.io/badge/version-0.9.0-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Ein moderner Twitch-Bot, der Song-Requests aus dem Twitch-Chat empfängt und über Spotify abspielt. Mit Warteschlange, Voting-System und Autopilot-Funktion.

## ✨ Features

- 🎵 **Song Requests**: Zuschauer können Songs per `!sr` Command anfordern
- 📊 **Smart Voting**: Songs mit mehr Votes werden priorisiert
- 🎯 **Queue Management**: Vollständige Kontrolle über die Warteschlange
- 🤖 **Autopilot**: Spielt automatisch Songs aus einer Playlist, wenn die Queue leer ist
- 🌍 **Multi-Language**: Deutsch & English
- 🎨 **Moderne UI**: Dark Theme mit CustomTkinter
- ⚙️ **Konfigurierbar**: Umfangreiche Einstellungsmöglichkeiten

## 📋 Voraussetzungen

- Python 3.9 oder höher
- Spotify Premium Account
- Twitch Account für den Bot
- Spotify Developer App

## 🚀 Installation

### 1. Repository klonen oder herunterladen

```bash
git clone https://github.com/yourusername/spotify-bot.git
cd spotify-bot
```

### 2. Virtual Environment erstellen (empfohlen)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

## ⚙️ Konfiguration

### Spotify App erstellen

1. Gehe zu [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Erstelle eine neue App
3. Notiere **Client ID** und **Client Secret**
4. Füge `http://127.0.0.1:8888/callback` als Redirect URI hinzu

### Twitch Token generieren

1. Besuche [Twitch Token Generator](https://twitchapps.com/tmi/)
2. Autorisiere den Bot-Account
3. Kopiere den OAuth Token

### Bot konfigurieren

1. Starte die Anwendung: `python app.py`
2. Klicke auf "Einstellungen ⚙️"
3. Trage folgende Daten ein:
   - **Twitch Kanal**: Dein Twitch-Kanalname (kleingeschrieben)
   - **Token**: OAuth Token vom Generator
   - **Spotify Client ID**: Von der Spotify Developer App
   - **Spotify Client Secret**: Von der Spotify Developer App
   - **Autopilot Playlist**: Link zu einer **öffentlichen** Spotify Playlist (optional)

## 🎮 Verwendung

### Bot starten

```bash
python app.py
```

1. Klicke auf **"STARTEN"**
2. Beim ersten Start: Spotify-Autorisierung im Browser
3. Bot ist online und bereit! ✅

### Chat Commands

```
!sr [Songname]          # Song suchen und hinzufügen
!sr [Spotify Link]      # Direkter Spotify Link
```

**Beispiele:**
```
!sr Never Gonna Give You Up
!sr https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
```

### GUI Funktionen

- **Smart Voting**: Songs mit mehr Votes werden höher priorisiert
- **▲/▼**: Songs manuell verschieben
- **📌**: Song an Position fixieren (verhindert Auto-Sortierung)
- **✕**: Song aus Queue entfernen
- **🗑 Alle löschen**: Queue komplett leeren
- **⏭ Skip**: Aktuellen Song überspringen
- **▶ Force Play**: Nächsten Song sofort abspielen

## 📁 Projektstruktur

```
SpotifyBot/
├── app.py                      # Haupteinstiegspunkt
├── requirements.txt            # Python-Dependencies
├── pyproject.toml             # Projekt-Konfiguration
├── README.md                  # Diese Datei
│
├── src/
│   ├── models/                # Datenmodelle
│   │   ├── song.py           # Song & QueueItem
│   │   └── config.py         # Konfigurationsmodelle
│   │
│   ├── services/              # Business Logic
│   │   ├── spotify_service.py    # Spotify API
│   │   ├── twitch_service.py     # Twitch Bot
│   │   ├── queue_manager.py      # Warteschlangen-Logik
│   │   └── bot_orchestrator.py   # Haupt-Koordinator
│   │
│   ├── ui/                    # GUI-Komponenten
│   │   ├── main_window.py    # Hauptfenster
│   │   ├── settings_window.py # Einstellungen
│   │   └── help_window.py    # Hilfe-Dialog
│   │
│   └── utils/                 # Hilfsfunktionen
│       ├── config_manager.py  # Config laden/speichern
│       ├── logging_config.py  # Logging-Setup
│       └── i18n.py           # Mehrsprachigkeit
│
├── locales/                   # Sprachdateien
│   ├── de.json               # Deutsch
│   └── en.json               # English
│
└── logs/                      # Log-Dateien (automatisch erstellt)
```

## 🔧 Konfigurationsoptionen

### Regeln & Limits

- **Max. Songs in Queue**: Maximale Anzahl gleichzeitiger Songs (Standard: 20)
- **Max. Wünsche pro User**: Songs pro Zuschauer in Queue (Standard: 3)
- **Max. Länge**: Maximale Song-Länge in Minuten (Standard: 10)
- **Cooldown**: Wartezeit in Minuten bis Song erneut gespielt werden kann (Standard: 30)

## 🛠️ Entwicklung

### Code-Stil

```bash
# Code formatieren
black src/

# Type Checking
mypy src/

# Linting
pylint src/
```

### Architektur

Das Projekt folgt modernen Python-Best-Practices:

- **Type Hints**: Vollständige Type Annotations
- **Async/Await**: Asynchrone Operationen für bessere Performance
- **Pydantic**: Config-Validation und Settings-Management
- **Dataclasses**: Saubere Datenmodelle
- **Logging**: Professional logging mit Rotation
- **Separation of Concerns**: Klare Trennung von GUI, Business Logic und Services

## 🐛 Troubleshooting

### Bot verbindet nicht

- ✅ Überprüfe Token und Credentials
- ✅ Stelle sicher, dass Spotify läuft
- ✅ Prüfe Internet-Verbindung

### Autopilot funktioniert nicht

- ✅ Playlist muss **"Öffentlich"** sein
- ✅ Korrekte Playlist-ID in Einstellungen
- ✅ Überprüfe Logs auf Fehler

### Songs werden nicht gespielt

- ✅ Spotify Premium Account erforderlich
- ✅ Spotify muss auf einem Gerät aktiv sein
- ✅ Device-ID wird automatisch erkannt

## 📝 Changelog

### Version 35.0 (Refactored)

- ✨ Komplett modernisierte Code-Basis
- 🏗️ Modulare Architektur mit Services
- 📦 Pydantic für Config-Management
- 🔄 Async/Await durchgängig
- 📊 Type Hints überall
- 📝 Professional Logging
- 🌍 Verbessertes I18N-System
- 🎨 Optimierte GUI-Struktur

### Version 34.0 (Legacy)

- Original Monolith-Version

## 📄 Lizenz

MIT License - siehe LICENSE Datei

## 👤 Autor

**uprisin6**

## 🙏 Danksagungen

- Spotify Web API
- TwitchIO
- CustomTkinter
- Pydantic

---

**Viel Spaß beim Streamen! 🎉**
