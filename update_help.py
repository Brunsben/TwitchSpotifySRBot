"""Update help texts with Smart Voting section."""
import json

# Read German locale
with open('locales/de.json', 'r', encoding='utf-8') as f:
    de = json.load(f)

# Read English locale
with open('locales/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)

# Update German help text
de['help']['text'] = """★ HILFE - TWITCH SR BOT v0.9.3 ★

Offizielle Dokumentation für den modernen EventSub-basierten Twitch Song Request Bot.

━━━ 1. ERSTE SCHRITTE ━━━

▸ TWITCH SETUP:
  1. Gehe zu https://dev.twitch.tv/console
  2. Erstelle eine neue App (z.B. 'MeinSRBot')
  3. OAuth Redirect URL: http://localhost:3000
  4. Notiere Client ID & Client Secret
  5. Im Bot: Klicke 'Einstellungen' → Tab 'Twitch Login'
  6. Trage Kanalnamen ein (z.B. 'uprisin6')
  7. Klicke auf den Token-Link für automatische OAuth2-Authentifizierung
  8. Scopes werden automatisch gesetzt (user:read:chat, user:write:chat, user:bot)

▸ SPOTIFY SETUP:
  1. Gehe zu https://developer.spotify.com/dashboard
  2. Erstelle eine neue App
  3. Redirect URI: http://localhost:8888/callback
  4. Notiere Client ID & Client Secret
  5. Im Bot: Tab 'Spotify API' → Trage die Daten ein
  6. Beim ersten Start öffnet sich der Browser für Login

━━━ 2. BERECHTIGUNGEN ━━━

▸ WER DARF SONGS WÜNSCHEN?
  • Alle: Jeder im Chat kann Songs wünschen
  • Nur Follower: User muss deinem Kanal folgen
  • Nur Subscribers: Nur Subs können Requests abgeben
  → Einstellbar in 'Regeln & Limits'

▸ FOLLOWER-PRÜFUNG:
  • Nutzt die Twitch Helix API
  • Ergebnis wird 5 Minuten gecached
  • Automatische Benachrichtigung im Chat

━━━ 3. REGELN & LIMITS ━━━

▸ Max. Songs in Queue: Maximale Warteschlangengröße (z.B. 10)
▸ Max. pro User: Wie viele Songs gleichzeitig von einem User (z.B. 2)
▸ Max. Länge: Maximale Song-Dauer in Minuten (z.B. 8)
▸ Cooldown: Minuten bis ein Song erneut gewünscht werden kann (z.B. 30)

━━━ 4. SMART VOTING ━━━

▸ WAS IST SMART VOTING?
  Wenn mehrere User denselben Song wünschen:
  • Song wird NICHT doppelt zur Queue hinzugefügt
  • Stattdessen erhält der Song +1 Vote
  • Songs mit mehr Votes rücken in der Queue nach oben
  • Demokratisches Song Request System!

▸ BEISPIEL:
  User1: !sr Bohemian Rhapsody → Song hinzugefügt (1 Vote)
  User2: !sr Bohemian Rhapsody → +1 Vote (jetzt 2 Votes)
  User3: !sr Bohemian Rhapsody → +1 Vote (jetzt 3 Votes)
  → Song steigt in der Warteschlange auf!

▸ EIN-/AUSSCHALTEN:
  • Toggle-Switch in der Haupt-GUI (rechts oben)
  • Kann jederzeit während des Betriebs geändert werden
  • Vote-Zahlen bleiben erhalten, werden nur nicht sortiert

━━━ 5. AUTOPILOT PLAYLIST ━━━

▸ ZWECK: Spielt automatisch Musik wenn Queue leer ist
▸ SETUP:
  1. Erstelle eine Playlist auf Spotify
  2. Setze sie auf ÖFFENTLICH (sehr wichtig!)
  3. Kopiere den Playlist-Link
  4. Füge ihn in 'Autopilot Playlist' ein
▸ Der Bot wechselt automatisch zwischen Requests und Autopilot

━━━ 6. CHAT COMMANDS ━━━

▸ FÜR ALLE USER:
  !sr <Songname>      - Sucht Song und fügt ihn hinzu
  !sr <Spotify-Link>  - Fügt Song direkt via Link hinzu
  !currentsong        - Zeigt aktuell laufenden Song

▸ NUR BROADCASTER/MODS:
  !skip               - Überspringt aktuellen Song

▸ BEISPIELE:
  !sr Never Gonna Give You Up
  !sr https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT

━━━ 7. GUI FUNKTIONEN ━━━

▸ HAUPT-CONTROLS:
  • STARTEN/STOPPEN: Bot-Verbindung steuern
  • Force Play: Spielt ausgewählten Song sofort
  • Skip: Überspringt aktuellen Song
  • Alle löschen: Leert die gesamte Queue
  • Smart Voting: Ein/Aus (Toggle rechts oben)

▸ DEBUG LOG:
  • Toggle-Button zeigt/verbirgt technische Logs
  • Hilfreich für Troubleshooting
  • Zeigt TwitchIO EventSub Events, API Calls, etc.

━━━ 8. TECHNISCHE INFO ━━━

▸ ARCHITEKTUR:
  • TwitchIO 3.x mit EventSub WebSocket
  • Keine IRC-Verbindung mehr (moderne API)
  • Spotify Web API mit OAuth2
  • Asynchrone Event-Verarbeitung

▸ FEATURES:
  ✓ Echtzeit Chat-Integration
  ✓ Automatische Token-Verwaltung
  ✓ Permission System mit API-Checks
  ✓ Smart Voting System (vote-basierte Queue-Sortierung)
  ✓ Multi-Language Support (DE/EN)
  ✓ Dark Mode UI

━━━ SUPPORT & LINKS ━━━

• GitHub: github.com/Brunsben/TwitchSpotifySRBot
• Twitch Dev Console: dev.twitch.tv/console
• Spotify Dashboard: developer.spotify.com/dashboard
• Troubleshooting: Siehe TROUBLESHOOTING.md im Repo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dev: uprisin6 | Version 0.9.3
Viel Spaß beim Streamen! 🎵"""

# Update English help text
en['help']['text'] = """★ HELP - TWITCH SR BOT v0.9.3 ★

Official documentation for the modern EventSub-based Twitch Song Request Bot.

━━━ 1. GETTING STARTED ━━━

▸ TWITCH SETUP:
  1. Go to https://dev.twitch.tv/console
  2. Create a new app (e.g., 'MySRBot')
  3. OAuth Redirect URL: http://localhost:3000
  4. Note down Client ID & Client Secret
  5. In Bot: Click 'Settings' → 'Twitch Login' tab
  6. Enter your channel name (e.g., 'uprisin6')
  7. Click the token link for automatic OAuth2 authentication
  8. Scopes are set automatically (user:read:chat, user:write:chat, user:bot)

▸ SPOTIFY SETUP:
  1. Go to https://developer.spotify.com/dashboard
  2. Create a new app
  3. Redirect URI: http://localhost:8888/callback
  4. Note down Client ID & Client Secret
  5. In Bot: 'Spotify API' tab → Enter credentials
  6. On first start, browser opens for login

━━━ 2. PERMISSIONS ━━━

▸ WHO CAN REQUEST SONGS?
  • Everyone: Anyone in chat can request
  • Followers Only: User must follow your channel
  • Subscribers Only: Only subs can make requests
  → Configurable in 'Rules & Limits'

▸ FOLLOWER CHECK:
  • Uses Twitch Helix API
  • Results cached for 5 minutes
  • Automatic chat notification

━━━ 3. RULES & LIMITS ━━━

▸ Max. Songs in Queue: Maximum queue size (e.g., 10)
▸ Max. per User: How many songs per user simultaneously (e.g., 2)
▸ Max. Length: Maximum song duration in minutes (e.g., 8)
▸ Cooldown: Minutes until a song can be requested again (e.g., 30)

━━━ 4. SMART VOTING ━━━

▸ WHAT IS SMART VOTING?
  When multiple users request the same song:
  • Song is NOT added twice to the queue
  • Instead, the song receives +1 Vote
  • Songs with more votes move up in the queue
  • Democratic song request system!

▸ EXAMPLE:
  User1: !sr Bohemian Rhapsody → Song added (1 Vote)
  User2: !sr Bohemian Rhapsody → +1 Vote (now 2 Votes)
  User3: !sr Bohemian Rhapsody → +1 Vote (now 3 Votes)
  → Song moves up in the queue!

▸ ENABLE/DISABLE:
  • Toggle switch in main GUI (top right)
  • Can be changed anytime during operation
  • Vote counts remain, just not sorted

━━━ 5. AUTOPILOT PLAYLIST ━━━

▸ PURPOSE: Automatically plays music when queue is empty
▸ SETUP:
  1. Create a playlist on Spotify
  2. Set it to PUBLIC (very important!)
  3. Copy the playlist link
  4. Paste it into 'Autopilot Playlist'
▸ Bot automatically switches between requests and autopilot

━━━ 6. CHAT COMMANDS ━━━

▸ FOR ALL USERS:
  !sr <songname>      - Searches and adds song
  !sr <Spotify-Link>  - Adds song directly via link
  !currentsong        - Shows currently playing song

▸ BROADCASTER/MODS ONLY:
  !skip               - Skips current song

▸ EXAMPLES:
  !sr Never Gonna Give You Up
  !sr https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT

━━━ 7. GUI FEATURES ━━━

▸ MAIN CONTROLS:
  • START/STOP: Control bot connection
  • Force Play: Play selected song immediately
  • Skip: Skip current song
  • Clear All: Empty entire queue
  • Smart Voting: On/Off (Toggle top right)

▸ DEBUG LOG:
  • Toggle button shows/hides technical logs
  • Helpful for troubleshooting
  • Shows TwitchIO EventSub events, API calls, etc.

━━━ 8. TECHNICAL INFO ━━━

▸ ARCHITECTURE:
  • TwitchIO 3.x with EventSub WebSocket
  • No IRC connection anymore (modern API)
  • Spotify Web API with OAuth2
  • Asynchronous event processing

▸ FEATURES:
  ✓ Real-time chat integration
  ✓ Automatic token management
  ✓ Permission system with API checks
  ✓ Smart voting system (vote-based queue sorting)
  ✓ Multi-language support (DE/EN)
  ✓ Dark mode UI

━━━ SUPPORT & LINKS ━━━

• GitHub: github.com/Brunsben/TwitchSpotifySRBot
• Twitch Dev Console: dev.twitch.tv/console
• Spotify Dashboard: developer.spotify.com/dashboard
• Troubleshooting: See TROUBLESHOOTING.md in repo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dev: uprisin6 | Version 0.9.3
Have fun streaming! 🎵"""

# Write updated files
with open('locales/de.json', 'w', encoding='utf-8') as f:
    json.dump(de, f, ensure_ascii=False, indent=2)

with open('locales/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)

print("✅ Help texts updated with Smart Voting section!")
