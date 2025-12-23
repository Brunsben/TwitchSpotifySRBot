# Changelog

All notable changes to Twitch SR Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.9] - 2025-12-23

### 🎉 Major Features

#### Flexible Command Permission System
- **5-Tier Permission Levels**: EVERYONE → FOLLOWERS → SUBSCRIBERS → MODERATORS → BROADCASTER
- **Per-Command Configuration**: Set individual permission levels for all 15 commands via GUI
- **Full GUI Integration**: New "Commands" tab in settings with dropdown menus for each command
- Replace old hardcoded permission system with flexible, user-configurable approach

#### 12 New Chat Commands (3 → 15 Total)
- **Queue Management**:
  - `!queue` - Display first 5 songs in queue (EVERYONE)
  - `!clearqueue` - Clear entire queue (MODERATORS)
  - `!pauserequests` - Pause song requests (MODERATORS)
  - `!resumerequests` - Resume song requests (MODERATORS)
  
- **Blacklist System**:
  - `!blacklist` - View blacklisted songs/artists (EVERYONE)
  - `!addblacklist <song/artist>` - Add to blacklist (MODERATORS)
  - `!removeblacklist <song/artist>` - Remove from blacklist (MODERATORS)
  
- **Song Information**:
  - `!songinfo` - Display detailed Spotify metadata (album, release date, duration, popularity) (EVERYONE)
  
- **User Features**:
  - `!wrongsong` / `!oops` - Remove own last request (EVERYONE)
  - `!srhelp` / `!commands` - Display all available commands with descriptions (EVERYONE)
  
- **Spotify Playback Control**:
  - `!pausesr` - Pause Spotify playback (MODERATORS)
  - `!resumesr` - Resume Spotify playback (MODERATORS)

#### Anti-Spam & Cooldown System
- **User-Cooldown**: Configurable per-user cooldown (default: 3 minutes, 0 = disabled)
- **Song-Cooldown**: Configurable per-song cooldown (default: 15 minutes, 0 = disabled)
- **GUI Integration**: Both cooldowns configurable in settings
- Cooldown bypass for moderators and broadcaster

#### Blacklist System
- **Dual Mode**: Block specific songs OR entire artists
- **Partial Matching**: Automatically matches song/artist names
- **Live Updates**: Changes apply immediately without restart
- **GUI Management**: Add/remove via settings or chat commands
- **Persistence**: Blacklist saved to config file

#### Duplicate Detection
- **Smart Voting Integration**: Only active when Smart Voting is OFF
- **Queue Scanning**: Prevents duplicate songs in queue
- **User Feedback**: Chat notification when duplicate detected
- Bypass for moderators and broadcaster

#### Spotify Status Monitoring
- **Real-Time Status Display**: GUI shows Spotify connection state
- **Visual Indicators**:
  - ✅ Spotify: Verbunden (green) - Active and connected
  - ⚠️ Spotify: Bitte starten! (orange) - Not running or no device
  - ❌ Spotify: Nicht verbunden (red) - Connection failed
- **Automatic Updates**: Status refreshes every few seconds
- **Error Handling**: Commands return user-friendly messages when Spotify offline

### 📚 Documentation

#### OBS Setup Guide (NEW)
- **340 lines** of comprehensive documentation
- **Full API Reference**: All WebSocket and REST endpoints documented
- **Code Examples**: JavaScript, Python, and cURL examples
- **Integration Guide**: Step-by-step setup for OBS Browser Source
- **Troubleshooting**: Common issues and solutions
- File: `OBS_SETUP.md`

#### Internationalization (i18n)
- **Complete German/English translations** for all new features
- **15 command descriptions** in both languages
- **Error messages** for all scenarios (Spotify offline, duplicate songs, cooldowns, etc.)
- **Help texts** updated to v0.9.9 (345 lines total per language)

### 🐛 Bug Fixes

1. **Twitch Connection Failed** (Critical)
   - Fixed parameter order in TwitchBotService constructor
   - Changed from positional to keyword arguments
   - Bot now connects to Twitch reliably

2. **Config Structure Confusion**
   - Corrected command_permissions location (BotConfig, not TwitchConfig)
   - TwitchBotService now receives full BotConfig and extracts Twitch sub-config
   - Settings save/load works correctly

3. **Spotify Client Reference**
   - Fixed incorrect `spotify.sp` usage
   - Changed to correct `spotify._client` reference
   - Metadata retrieval now works (songinfo command)

4. **Resume Playback Bug** (Critical)
   - Fixed `resumesr` starting new track instead of resuming paused one
   - Added playback state check before resume
   - Only calls `start_playback()` if currently paused
   - Playback resumes at same position

5. **Missing Error Handling for Offline Spotify**
   - Added try/except blocks to pause/resume handlers
   - Exceptions now re-raised from SpotifyService methods
   - User receives "Spotify spielt gerade nichts ab" when offline
   - Handles connection timeouts, device errors, API failures

### 🔧 Technical Changes

- **BotOrchestrator**: 15 command callbacks, state management for requests pause
- **QueueManager**: requests_paused parameter, RequestResult.REQUESTS_PAUSED enum
- **SpotifyService**: pause_playback(), resume_playback() with state checks
- **TwitchService**: Generic _check_command_permission() method, 15 command handlers
- **Settings GUI**: New "Commands" tab with permission dropdowns for all 15 commands
- **Main Window**: Request status indicator, Spotify status indicator with auto-update

### 📊 Statistics

- **Commands**: 3 → **15** (+400%)
- **Permission Levels**: 2 → **5** (+150%)
- **Documentation**: +340 lines (OBS_SETUP.md)
- **i18n Entries**: +45 keys (DE/EN)
- **Code Files Modified**: 12 files
- **Bug Fixes**: 5 critical issues resolved

### ⚙️ Configuration

New config entries:
- `user_cooldown_seconds` (int, default: 180)
- `song_cooldown_minutes` (int, default: 15)
- `blacklist` (list of strings)
- `command_permissions` (CommandPermissions object with 15 fields)
- `requests_paused` (bool, default: false)

---

## [0.9.8] - 2025-12-XX

### Features
- Modern GUI with CustomTkinter
- Spotify integration with Spotipy
- Twitch bot with TwitchIO (EventSub WebSocket)
- OBS overlay with WebSocket + REST API
- Smart Voting system
- Basic chat commands (!sr, !skip, !currentsong)

### Technical
- Python 3.13.7
- Async/await architecture
- Pydantic 2.x config validation
- i18n support (German/English)

---

## Previous Versions

See Git history for older releases.
