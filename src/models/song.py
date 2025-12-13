"""Song and queue item models."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Song:
    """Represents a Spotify track."""
    
    name: str
    uri: str
    duration_ms: int
    artist: str
    
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
