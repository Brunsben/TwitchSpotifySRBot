"""Song and queue item models."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Song:
    """Represents a Spotify track."""
    
    name: str
    uri: str
    duration_ms: int
    artist: str
    cover_url: str = ""  # Album cover image URL
    
    @property
    def duration_str(self) -> str:
        """Return formatted duration (MM:SS)."""
        seconds = int((self.duration_ms / 1000) % 60)
        minutes = int((self.duration_ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"
    
    @property
    def full_name(self) -> str:
        """Return full song name with artist."""
        return f"{self.name} - {self.artist}"


@dataclass
class QueueItem:
    """Represents a song in the queue with metadata."""
    
    song: Song
    votes: int = 1
    requesters: List[str] = field(default_factory=list)
    is_manual: bool = False  # Pinned by admin
    
    @property
    def name(self) -> str:
        """Shortcut to song name."""
        return self.song.name
    
    @property
    def uri(self) -> str:
        """Shortcut to song URI."""
        return self.song.uri
    
    @property
    def duration_ms(self) -> int:
        """Shortcut to song duration."""
        return self.song.duration_ms
    
    @property
    def requesters_str(self) -> str:
        """Return comma-separated requester names."""
        return ", ".join(self.requesters)


@dataclass
class HistoryEntry:
    """Represents a played song in the history."""
    
    song_name: str
    artist: str
    uri: str
    duration_ms: int
    requester: str  # Username who requested (or "Autopilot")
    timestamp: datetime
    was_skipped: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "song_name": self.song_name,
            "artist": self.artist,
            "uri": self.uri,
            "duration_ms": self.duration_ms,
            "requester": self.requester,
            "timestamp": self.timestamp.isoformat(),
            "was_skipped": self.was_skipped
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'HistoryEntry':
        """Create HistoryEntry from dictionary."""
        return HistoryEntry(
            song_name=data["song_name"],
            artist=data["artist"],
            uri=data["uri"],
            duration_ms=data["duration_ms"],
            requester=data["requester"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            was_skipped=data.get("was_skipped", False)
        )
