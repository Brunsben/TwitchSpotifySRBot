# 🚀 GitHub Upload Checkliste

## ✅ Sicherheits-Check (ERLEDIGT)

- ✅ Hardcoded Credentials entfernt (test_twitch.py → Environment Variables)
- ✅ .gitignore erstellt (config_premium.json, .env, .cache, logs/)
- ✅ .env.example für Template erstellt
- ✅ LICENSE (MIT) hinzugefügt
- ✅ Keine Secrets in src/ gefunden
- ✅ Kein config_premium.json im Repo
- ✅ Kein .cache im Repo

## 📋 Nächste Schritte

### 1. Git Repository initialisieren

```bash
cd f:\Programmieren\SpotifyBot
git init
git add .
git commit -m "Initial commit - Twitch SR Bot v0.9.0"
```

### 2. GitHub Repository erstellen

1. Gehe zu <https://github.com/new>
2. Repository Name: `TwitchSRBot` (oder ein anderer Name)
3. Description: "Modern Spotify Song Request Bot for Twitch with EventSub, GUI and Permission System"
4. **Wichtig**: NICHT "Initialize with README" anklicken (haben wir schon!)
5. **Public** oder **Private** wählen
6. Repository erstellen

### 3. Mit GitHub verbinden & pushen

```bash
# Remote hinzufügen (URL von GitHub kopieren!)
git remote add origin https://github.com/DEIN_USERNAME/TwitchSRBot.git

# Branch umbenennen zu main (falls nötig)
git branch -M main

# Push
git push -u origin main
```

## 📝 Was ist im Repository?

### ✅ Included (sicher zum Upload)

- Gesamter Source Code (src/)
- UI-Komponenten (CustomTkinter)
- Dokumentation (README.md, INSTALL.md, BUILD.md, TROUBLESHOOTING.md)
- Build-Konfiguration (pyproject.toml, requirements.txt, build.py)
- Übersetzungen (locales/de.json, en.json)
- Legacy Backup (zur Referenz)
- .env.example (Template ohne Secrets)
- LICENSE (MIT)

### ❌ Excluded (in .gitignore)

- config_premium.json (deine persönliche Config!)
- .cache* (Spotify Token Cache)
- logs/ (Log-Dateien)
- **pycache**/ (Python Cache)
- test_twitch.py (Test-Datei mit Env-Vars)
- build/, dist/ (Build-Artefakte)
- .env (persönliche Environment Variables)

## 🔒 Nach dem Upload

1. **Überprüfe das GitHub-Repo**:
   - Klick durch die Dateien
   - Prüfe ob `config_premium.json` NICHT sichtbar ist
   - Prüfe ob keine Tokens/Secrets sichtbar sind

2. **Release erstellen** (optional):

   ```bash
   # .exe bauen
   python build.py
   
   # Auf GitHub: Releases → Create new release
   # Tag: v0.9.0
   # Upload: dist/TwitchSRBot.exe
   ```

3. **Repository Topics hinzufügen** (auf GitHub):

   - `twitch-bot`
   - `spotify-api`
   - `twitchio`
   - `python`
   - `song-requests`
   - `customtkinter`
   - `eventsub`

## 💡 Tipps

- **Private Repository** empfohlen, wenn du später noch persönliche Anpassungen machst
- **Public Repository** wenn du es Open Source machen willst
- Branch Protection für `main` aktivieren (Settings → Branches)
- GitHub Actions für automatische Builds nutzen (optional)

## 🆘 Falls etwas schiefgeht

### Versehentlich Secrets gepusht

```bash
# Letzte Commits rückgängig machen (VORSICHT!)
git reset --soft HEAD~1

# Oder bestimmte Datei entfernen
git rm --cached config_premium.json
git commit -m "Remove sensitive config"
git push --force
```

**WICHTIG**: Wenn Tokens öffentlich waren, sofort:

1. Twitch App → Reset Client Secret
2. Spotify App → Reset Client Secret  
3. Neue OAuth Tokens generieren

## ✨ Fertig

Dein Bot ist jetzt ready für GitHub! 🎉

Nach dem Upload kannst du:

- Issues für Feature-Requests nutzen
- Wiki für erweiterte Docs erstellen
- GitHub Projects für Roadmap nutzen
- Contributors hinzufügen
