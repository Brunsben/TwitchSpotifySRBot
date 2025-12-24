# Migration Guide: V34 → V35

## 🎯 Was ist neu?

Die V35 ist eine **komplette Neuschreibung** des Bots mit modernen Python-Best-Practices.

## 📊 Vergleich Alt vs. Neu

| Aspekt              | V34 (Alt)                   | V35 (Neu)                              |
| ------------------- | --------------------------- | -------------------------------------- |
| **Dateien**         | 1 Monolith (787 Zeilen)     | Modulare Struktur (15+ Dateien)        |
| **Architektur**     | Alles in einer Klasse       | Services, Models, Utils getrennt       |
| **Async**           | Teilweise mit Threads       | Durchgängig async/await                |
| **Type Hints**      | Keine                       | Vollständig typisiert                  |
| **Config**          | JSON + Dictionary           | Pydantic Models mit Validation         |
| **Logging**         | print() Statements          | Professional logging Framework         |
| **Error Handling**  | try/except minimal          | Umfangreich in allen Services          |
| **Testing**         | Nicht möglich               | Testbar durch Dependency Injection     |

## 🏗️ Neue Architektur

### Models (`src/models/`)

- **song.py**: Song & QueueItem Dataclasses
- **config.py**: Pydantic Config Models mit Validation

### Services (`src/services/`)

- **spotify_service.py**: Spotify API Wrapper (async)
- **twitch_service.py**: Twitch Bot Service
- **queue_manager.py**: Queue Logic mit Voting
- **bot_orchestrator.py**: Koordiniert alle Services

### UI (`src/ui/`)

- **main_window.py**: Haupt-GUI
- **settings_window.py**: Einstellungen-Dialog
- **help_window.py**: Hilfe-Fenster

### Utils (`src/utils/`)

- **config_manager.py**: Config laden/speichern
- **logging_config.py**: Logging Setup
- **i18n.py**: Internationalisierung

## ✨ Hauptverbesserungen

### 1. **Separation of Concerns**

Jede Komponente hat eine klare Verantwortung:

```python
# Alt: Alles in BotGUI
class BotGUI:
    def run_process(self): ...  # Spotify + Twitch + Queue
    
# Neu: Getrennte Services
class SpotifyService: ...
class TwitchBotService: ...
class QueueManager: ...
class BotOrchestrator: ...  # Koordiniert
```

### 2. **Type Safety**

```python
# Alt
def handle_request_sync(self, query, user):
    track = None  # Was ist das?
    
# Neu
async def add_request(self, song: Song, username: str) -> RequestResult:
    """Add a song request to the queue."""
```

### 3. **Config Validation**

```python
# Alt
max_q = int(self.config_data.get('max_queue', 20))  # Runtime Error möglich

# Neu
class RulesConfig(BaseModel):
    max_queue_size: int = Field(default=20, ge=1)  # Validiert beim Laden
```

### 4. **Async/Await**

```python
# Alt
loop.run_in_executor(None, lambda: self._client.search(...))

# Neu
async def search_track(self, query: str) -> Optional[Song]:
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(...)
```

### 5. **Professional Logging**

```python
# Alt
print("Spotify connected.")

# Neu
logger = logging.getLogger(__name__)
logger.info("Successfully connected to Spotify")
# + Rotation, Levels, File Output
```

### 6. **Error Handling**

```python
# Alt
try:
    track = self.sp_client.track(query)
except: pass  # Fehler verschwindet

# Neu
except Exception as e:
    logger.error(f"Error searching track '{query}': {e}")
    return None
```

## 🔄 Migration

### Automatisch

```bash
python migrate.py
```

- Sichert alte `main.py` → `legacy/`
- Erstellt benötigte Ordner
- Config wird automatisch konvertiert

### Config-Kompatibilität

Die alte `config_premium.json` wird automatisch in das neue Format konvertiert:

```json
// Alt
{
  "sp_id": "abc",
  "max_queue": "20"
}

// Wird zu
{
  "spotify": {
    "client_id": "abc"
  },
  "rules": {
    "max_queue_size": 20
  }
}
```

## 🎓 Code-Qualität

### Erweiterbarkeit

```python
# Neuen Service hinzufügen:
class NewService:
    async def do_something(self): ...

# In BotOrchestrator integrieren:
class BotOrchestrator:
    def __init__(self):
        self.new_service = NewService()
```

### Testbarkeit

```python
# Services sind unabhängig testbar:
async def test_spotify_search():
    service = SpotifyService(mock_config)
    song = await service.search_track("test")
    assert song is not None
```

### Wartbarkeit

- Klare Datei-Struktur
- Dokumentierte Funktionen
- Type Hints für IDE-Support
- Logging für Debugging

## 📈 Performance

- **Async**: Keine blockierenden Operationen
- **Threading**: Twitch läuft in separatem Thread
- **Event Loop**: Effiziente Task-Verwaltung

## 🛡️ Robustheit

- **Pydantic Validation**: Config-Fehler beim Start erkannt
- **Error Recovery**: Services können Fehler überleben
- **Logging**: Alle Fehler werden protokolliert
- **Type Checking**: mypy findet Bugs vor Runtime

## 🔮 Zukunft

Die neue Architektur ermöglicht einfach:

- Unit Tests hinzufügen
- Weitere Streaming-Plattformen (YouTube, etc.)
- REST API für externe Steuerung
- Database Backend statt JSON
- Plugin-System
- Docker Deployment

## 📝 Breaking Changes

**Keine!** Die neue Version ist abwärtskompatibel:

- Alte Config wird konvertiert
- GUI ist identisch
- Commands bleiben gleich
- Funktionalität unverändert

## 🎉 Fazit

V35 ist **production-ready** und folgt allen modernen Python-Best-Practices:

- ✅ PEP 8 konform
- ✅ Type Hints (PEP 484)
- ✅ Async/Await (PEP 492)
- ✅ Dataclasses (PEP 557)
- ✅ Modern packaging (PEP 621)

**Der Code ist jetzt wartbar, testbar und erweiterbar!** 🚀
