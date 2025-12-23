# 🎥 OBS Overlay Setup Guide

Der Twitch SR Bot enthält ein integriertes **Live Overlay System** für OBS, das den aktuellen Song mit Cover Art, Artist und Requester anzeigt.

## 🚀 Quick Start (OBS Browser Source)

### Schritt 1: Bot starten
Starte den TwitchSRBot - der Overlay-Server läuft automatisch auf **Port 8080**.

### Schritt 2: OBS Browser Source hinzufügen

1. **In OBS**: Rechtsklick auf Szene → "Hinzufügen" → "Browser"
2. **Name**: "Now Playing" (oder beliebig)
3. **URL**: `http://localhost:8080`
4. **Breite**: `800` (empfohlen)
5. **Höhe**: `200` (empfohlen)
6. ✅ **"Lokale Datei"** NICHT aktivieren
7. ✅ **"Seite neu laden, wenn Szene aktiv wird"** aktivieren (optional)
8. Klicke "OK"

### Schritt 3: Position & Styling
- Positioniere das Overlay in deiner Szene (z.B. unten links/rechts)
- Das Overlay ist **transparent** und fügt sich nahtlos ein
- Größe kann beliebig skaliert werden

### Fertig! 🎉
Das Overlay aktualisiert sich **automatisch in Echtzeit** via WebSocket, sobald ein neuer Song spielt.

---

## 📡 API Dokumentation

Der Overlay-Server bietet 3 Endpoints für verschiedene Anwendungsfälle:

### 1. HTML Overlay (OBS)
**Endpoint:** `http://localhost:8080/`  
**Verwendung:** OBS Browser Source  
**Features:**
- Live-Updates via WebSocket
- Album Cover Art
- Song Name, Artist, Requester
- Twitch → Spotify Gradient Design
- Smooth Animationen

### 2. WebSocket (Custom Overlays)
**Endpoint:** `ws://localhost:8080/ws`  
**Protokoll:** WebSocket  
**Verwendung:** Eigene Custom Overlays

**Nachrichtenformat (JSON):**
```json
{
  "name": "Bohemian Rhapsody",
  "artist": "Queen",
  "cover_url": "https://i.scdn.co/image/...",
  "requester": "username123"
}
```

**Beispiel (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const song = JSON.parse(event.data);
  console.log(`Now playing: ${song.name} by ${song.artist}`);
  console.log(`Requested by: ${song.requester}`);
};
```

### 3. REST API (Polling)
**Endpoint:** `GET http://localhost:8080/api/current`  
**Format:** JSON  
**Verwendung:** Apps, Scripts, externe Tools

**Response:**
```json
{
  "name": "Never Gonna Give You Up",
  "artist": "Rick Astley",
  "cover_url": "https://i.scdn.co/image/ab67616d0000b273...",
  "requester": "rickroll42"
}
```

**Beispiel (cURL):**
```bash
curl http://localhost:8080/api/current
```

**Beispiel (Python):**
```python
import requests

response = requests.get('http://localhost:8080/api/current')
song = response.json()
print(f"{song['name']} - {song['artist']}")
```

---

## 🎨 Overlay Design

### Standard Design
- **Hintergrund:** Transparent (für OBS)
- **Gradient:** Twitch Lila (`#9146FF`) → Spotify Grün (`#1DB954`)
- **Schrift:** Segoe UI, weiß mit Schatten
- **Cover:** 150x150px mit abgerundeten Ecken
- **Animation:** Slide-in bei Song-Wechsel

### Custom Styling
Du kannst das HTML/CSS im Code anpassen:  
`src/services/obs_overlay.py` → Methode `_get_overlay_html()`

**Beispiel-Anpassungen:**
```css
/* Größere Schrift */
.song-name {
    font-size: 32px !important;
}

/* Anderer Hintergrund */
.container {
    background: rgba(0, 0, 0, 0.8);
    border-radius: 15px;
}

/* Andere Farben */
.container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

---

## 🔧 Erweiterte Konfiguration

### Port ändern
Standardmäßig läuft der Server auf **Port 8080**. Zum Ändern:

**In `src/services/bot_orchestrator.py` (Zeile 37):**
```python
self.obs_overlay = OBSOverlayServer(port=8080)  # ← Hier ändern
```

**Dann in OBS die URL anpassen:**
```
http://localhost:DEIN_PORT
```

### Mehrere Overlays
Du kannst dieselbe Quelle mehrfach hinzufügen:
- **Overlay 1:** Vollständige Info (Name, Artist, Cover)
- **Overlay 2:** Nur Song-Name (mit CSS-Filter)
- **Overlay 3:** Nur Cover (mit CSS-Filter)

Jedes nutzt dieselbe URL, aber du stylst sie in OBS unterschiedlich (z.B. mit Cropping).

### Overlay ausblenden wenn leer
Das Overlay zeigt "No song playing" wenn kein Song läuft. Du kannst es in OBS mit einer **Bedingung** verknüpfen, um es automatisch auszublenden.

---

## 🐛 Troubleshooting

### Overlay zeigt nichts in OBS
1. ✅ Bot läuft? (Check Terminal/Logs)
2. ✅ URL korrekt? (`http://localhost:8080`)
3. ✅ Port 8080 frei? (kein anderes Programm nutzt ihn)
4. ✅ Firewall blockiert nicht?
5. ✅ Browser Source Breite/Höhe groß genug?

**Test:** Öffne `http://localhost:8080` im Browser - sollte das Overlay zeigen.

### Overlay aktualisiert sich nicht
1. ✅ Song spielt tatsächlich? (Check Spotify)
2. ✅ WebSocket-Verbindung aktiv? (Check Browser-Konsole: F12)
3. ✅ Bot sendet Updates? (Check Debug-Log im Bot)

**Fix:** Browser Source in OBS refreshen (Rechtsklick → "Aktualisieren")

### Cover Art wird nicht angezeigt
- Spotify gibt nicht immer Cover-URLs zurück
- Fallback: Musiknote-Emoji 🎵
- Cover erscheint nur bei Spotify-Tracks, nicht bei Local Files

### Overlay reagiert verzögert
- WebSocket sollte instant sein (~50-200ms)
- Bei Verzögerung: Check CPU-Auslastung & Netzwerk
- OBS Browser Source hat eingebautes Caching

### Port bereits belegt
**Fehler:** `Address already in use: 8080`

**Lösung 1:** Port ändern (siehe "Erweiterte Konfiguration")  
**Lösung 2:** Anderes Programm auf Port 8080 beenden
```bash
# Windows: Port prüfen
netstat -ano | findstr :8080

# Prozess beenden
taskkill /PID <PID> /F
```

---

## 💡 Tipps & Tricks

### Tipp 1: Animationen deaktivieren
Für cleane, statische Overlays:
```css
/* In _get_overlay_html() hinzufügen */
.container {
    animation: none !important;
}
```

### Tipp 2: Kompaktes Layout
Für weniger Platz:
```
Breite: 600px
Höhe: 120px
```

### Tipp 3: Requester Name hervorheben
```css
.requester {
    color: #1DB954;
    font-weight: bold;
}
```

### Tipp 4: Mobile-freundlich
Das Overlay funktioniert auch auf mobilen Geräten im Browser:
```
http://DEINE_IP:8080
```
(Nützlich für Monitoring auf Tablet/Handy)

### Tipp 5: Mehrsprachigkeit
Die Labels sind hardcoded als "NOW PLAYING". Für andere Sprachen:
```html
<div class="label">JETZT LÄUFT</div>  <!-- Deutsch -->
<div class="label">EN COURS</div>     <!-- Französisch -->
```

---

## 🔗 Integration mit anderen Tools

### Stream Deck
Nutze die REST API um Song-Info auf Stream Deck-Buttons anzuzeigen:
- Plugin: "API Ninja" oder "SuperMacro"
- URL: `http://localhost:8080/api/current`
- Update-Intervall: 2-5 Sekunden

### Discord Bot
Zeige Now Playing in Discord:
```python
import discord
import requests

@bot.command()
async def nowplaying(ctx):
    response = requests.get('http://localhost:8080/api/current')
    song = response.json()
    await ctx.send(f"🎵 {song['name']} - {song['artist']}")
```

### Twitch Chat Bot (anderer)
Integriere mit anderem Bot (z.B. Nightbot):
```
$(urlfetch http://localhost:8080/api/current)
```

---

## 📚 Weitere Ressourcen

- **GitHub:** [Brunsben/TwitchSpotifySRBot](https://github.com/Brunsben/TwitchSpotifySRBot)
- **Issues:** Bug Reports & Feature Requests
- **Discussions:** Community Support
- **README.md:** Allgemeine Bot-Dokumentation
- **TROUBLESHOOTING.md:** Allgemeine Problemlösungen

---

## ❓ FAQ

**Q: Kann ich mehrere Bots mit einem Overlay nutzen?**  
A: Nein, Port 8080 kann nur von einem Bot gleichzeitig genutzt werden. Du könntest aber verschiedene Ports konfigurieren.

**Q: Funktioniert es auch remote (nicht localhost)?**  
A: Ja! Ändere in OBS die URL auf `http://DEINE_IP:8080`. Stelle sicher, dass die Firewall den Port freigibt.

**Q: Kann ich das Overlay auch außerhalb von OBS nutzen?**  
A: Ja! Öffne einfach `http://localhost:8080` in jedem modernen Browser. Funktioniert auch auf Mobilgeräten.

**Q: Unterstützt es mehrere Viewer gleichzeitig?**  
A: Ja! Unbegrenzt viele WebSocket-Clients können gleichzeitig verbunden sein.

**Q: Kann ich eigene Designs erstellen?**  
A: Absolut! Du kannst das HTML/CSS im Code anpassen oder komplett eigene Overlays mit der WebSocket/REST API bauen.

---

**Viel Erfolg beim Streaming! 🎵✨**
