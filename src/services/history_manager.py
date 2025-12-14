"""History tracking and statistics for played songs."""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import Counter

from ..models.song import HistoryEntry, Song

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages song play history and statistics."""
    
    def __init__(self, history_file: str = "config/history.json"):
        """Initialize history manager.
        
        Args:
            history_file: Path to history JSON file
        """
        self.history_file = Path(history_file)
        self.history: List[HistoryEntry] = []
        self._load_history()
    
    def add_entry(self, song: Song, requester: str, was_skipped: bool = False) -> None:
        """Add a song to the history.
        
        Args:
            song: The song that was played
            requester: Username who requested (or "Autopilot")
            was_skipped: Whether the song was skipped
        """
        entry = HistoryEntry(
            song_name=song.name,
            artist=song.artist,
            uri=song.uri,
            duration_ms=song.duration_ms,
            requester=requester,
            timestamp=datetime.now(),
            was_skipped=was_skipped
        )
        
        self.history.append(entry)
        logger.info(f"Added to history: {song.full_name} by {requester}")
        
        # Auto-save after each entry
        self._save_history()
    
    def get_top_songs(self, limit: int = 10, days: int = 0) -> List[Tuple[str, str, int]]:
        """Get most requested songs.
        
        Args:
            limit: Number of songs to return
            days: Filter to last N days (0 = all time)
            
        Returns:
            List of tuples: (song_name, artist, play_count)
        """
        filtered = self._filter_by_days(days)
        
        # Count by song URI
        song_counts = Counter((entry.song_name, entry.artist, entry.uri) for entry in filtered)
        
        # Sort by count and return top N
        top = song_counts.most_common(limit)
        return [(name, artist, count) for (name, artist, _), count in top]
    
    def get_top_requesters(self, limit: int = 10, days: int = 0) -> List[Tuple[str, int]]:
        """Get users who requested the most songs.
        
        Args:
            limit: Number of requesters to return
            days: Filter to last N days (0 = all time)
            
        Returns:
            List of tuples: (username, request_count)
        """
        filtered = self._filter_by_days(days)
        
        # Exclude autopilot
        user_requests = [e.requester for e in filtered if e.requester.lower() != "autopilot"]
        
        requester_counts = Counter(user_requests)
        return requester_counts.most_common(limit)
    
    def get_top_artists(self, limit: int = 10, days: int = 0) -> List[Tuple[str, int]]:
        """Get most played artists.
        
        Args:
            limit: Number of artists to return
            days: Filter to last N days (0 = all time)
            
        Returns:
            List of tuples: (artist, play_count)
        """
        filtered = self._filter_by_days(days)
        
        artist_counts = Counter(entry.artist for entry in filtered)
        return artist_counts.most_common(limit)
    
    def get_stats_summary(self, days: int = 0) -> Dict:
        """Get summary statistics.
        
        Args:
            days: Filter to last N days (0 = all time)
            
        Returns:
            Dictionary with various stats
        """
        filtered = self._filter_by_days(days)
        
        if not filtered:
            return {
                "total_songs": 0,
                "unique_songs": 0,
                "total_requesters": 0,
                "skip_rate": 0.0,
                "autopilot_percentage": 0.0,
                "total_duration_hours": 0.0
            }
        
        unique_songs = len(set(e.uri for e in filtered))
        unique_requesters = len(set(e.requester for e in filtered if e.requester.lower() != "autopilot"))
        skipped = sum(1 for e in filtered if e.was_skipped)
        autopilot = sum(1 for e in filtered if e.requester.lower() == "autopilot")
        total_duration_ms = sum(e.duration_ms for e in filtered)
        
        return {
            "total_songs": len(filtered),
            "unique_songs": unique_songs,
            "total_requesters": unique_requesters,
            "skip_rate": (skipped / len(filtered) * 100) if filtered else 0,
            "autopilot_percentage": (autopilot / len(filtered) * 100) if filtered else 0,
            "total_duration_hours": total_duration_ms / (1000 * 60 * 60)
        }
    
    def export_to_json(self, filepath: str) -> None:
        """Export history to JSON file.
        
        Args:
            filepath: Output file path
        """
        data = [entry.to_dict() for entry in self.history]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(self.history)} entries to {filepath}")
    
    def export_to_csv(self, filepath: str) -> None:
        """Export history to CSV file.
        
        Args:
            filepath: Output file path
        """
        import csv
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Song', 'Artist', 'Requester', 'Skipped', 'Duration (min)'])
            
            for entry in self.history:
                duration_min = entry.duration_ms / (1000 * 60)
                writer.writerow([
                    entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    entry.song_name,
                    entry.artist,
                    entry.requester,
                    'Yes' if entry.was_skipped else 'No',
                    f"{duration_min:.2f}"
                ])
        
        logger.info(f"Exported {len(self.history)} entries to {filepath}")
    
    def clear_history(self) -> None:
        """Clear all history entries."""
        self.history.clear()
        self._save_history()
        logger.info("History cleared")
    
    def _filter_by_days(self, days: int) -> List[HistoryEntry]:
        """Filter history entries by number of days.
        
        Args:
            days: Number of days to filter (0 = all time)
            
        Returns:
            Filtered list of history entries
        """
        if days <= 0:
            return self.history
        
        cutoff = datetime.now() - timedelta(days=days)
        return [e for e in self.history if e.timestamp >= cutoff]
    
    def _load_history(self) -> None:
        """Load history from JSON file."""
        if not self.history_file.exists():
            logger.info("No history file found, starting with empty history")
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.history = [HistoryEntry.from_dict(entry) for entry in data]
            logger.info(f"Loaded {len(self.history)} entries from history")
            
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.history = []
    
    def _save_history(self) -> None:
        """Save history to JSON file."""
        try:
            # Create directory if it doesn't exist
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = [entry.to_dict() for entry in self.history]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
