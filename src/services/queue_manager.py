"""Queue manager for handling song queue logic."""
import asyncio
import logging
import time
from typing import List, Optional, Dict
from enum import Enum

from ..models.song import Song, QueueItem
from ..models.config import RulesConfig

logger = logging.getLogger(__name__)


class RequestResult(Enum):
    """Result of a song request."""
    
    SUCCESS = "success"
    QUEUE_FULL = "queue_full"
    USER_LIMIT = "user_limit"
    TOO_LONG = "too_long"
    ON_COOLDOWN = "on_cooldown"
    NOT_FOUND = "not_found"
    VOTED = "voted"


class QueueManager:
    """Manages the song queue with voting and rules."""
    
    def __init__(self, rules: RulesConfig, smart_voting_enabled: bool = True):
        """Initialize queue manager.
        
        Args:
            rules: Queue rules configuration
            smart_voting_enabled: Whether to enable smart voting
        """
        self.rules = rules
        self.smart_voting_enabled = smart_voting_enabled
        
        self._queue: List[QueueItem] = []
        self._history: Dict[str, float] = {}  # URI -> timestamp
        self._lock = asyncio.Lock()
    
    @property
    def queue(self) -> List[QueueItem]:
        """Get current queue (read-only copy)."""
        return self._queue.copy()
    
    @property
    def total_duration_ms(self) -> int:
        """Get total duration of all queued songs in milliseconds."""
        return sum(item.duration_ms for item in self._queue)
    
    def get_user_request_count(self, username: str) -> int:
        """Get number of active requests for a user.
        
        Args:
            username: Username to check
            
        Returns:
            Number of songs requested by user
        """
        count = 0
        for item in self._queue:
            if username in item.requesters:
                count += 1
        return count
    
    async def add_request(self, song: Song, username: str) -> RequestResult:
        """Add a song request to the queue.
        
        Args:
            song: Song to add
            username: Username making the request
            
        Returns:
            RequestResult indicating success or failure reason
        """
        async with self._lock:
            # Check queue size
            if len(self._queue) >= self.rules.max_queue_size:
                return RequestResult.QUEUE_FULL
            
            # Check user limit
            if self.get_user_request_count(username) >= self.rules.max_user_requests:
                return RequestResult.USER_LIMIT
            
            # Check song length
            max_duration_ms = self.rules.max_song_length_minutes * 60 * 1000
            if song.duration_ms > max_duration_ms:
                return RequestResult.TOO_LONG
            
            # Check if song already in queue
            existing = self._find_in_queue(song.uri)
            if existing:
                if self.smart_voting_enabled and username not in existing.requesters:
                    existing.votes += 1
                    existing.requesters.append(username)
                    logger.info(f"Vote added for {song.full_name} by {username} ({existing.votes} votes)")
                    await self._sort_queue()
                    return RequestResult.VOTED
                else:
                    return RequestResult.VOTED
            
            # Check cooldown
            if self._is_on_cooldown(song.uri):
                return RequestResult.ON_COOLDOWN
            
            # Add to queue
            queue_item = QueueItem(
                song=song,
                votes=1,
                requesters=[username],
                is_manual=False
            )
            
            self._queue.append(queue_item)
            logger.info(f"Added {song.full_name} to queue (requested by {username})")
            
            await self._sort_queue()
            return RequestResult.SUCCESS
    
    async def remove_item(self, index: int) -> bool:
        """Remove an item from the queue.
        
        Args:
            index: Index of item to remove
            
        Returns:
            True if removed, False if index invalid
        """
        async with self._lock:
            if 0 <= index < len(self._queue):
                removed = self._queue.pop(index)
                logger.info(f"Removed {removed.song.full_name} from queue")
                return True
            return False
    
    async def clear_queue(self) -> None:
        """Clear all items from the queue."""
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            logger.info(f"Cleared {count} items from queue")
    
    async def pop_next(self) -> Optional[QueueItem]:
        """Remove and return the next item from the queue.
        
        Returns:
            Next QueueItem or None if queue empty
        """
        async with self._lock:
            if not self._queue:
                return None
            
            item = self._queue.pop(0)
            
            # Add to history
            self._history[item.uri] = time.time()
            
            logger.info(f"Popped {item.song.full_name} from queue")
            return item
    
    async def move_item(self, from_index: int, to_index: int) -> bool:
        """Move an item in the queue.
        
        Args:
            from_index: Source index
            to_index: Destination index
            
        Returns:
            True if moved successfully
        """
        async with self._lock:
            if not (0 <= from_index < len(self._queue) and 
                    0 <= to_index < len(self._queue)):
                return False
            
            item = self._queue.pop(from_index)
            item.is_manual = True  # Mark as manually positioned
            self._queue.insert(to_index, item)
            
            logger.info(f"Moved {item.song.full_name} from {from_index} to {to_index}")
            return True
    
    async def pin_item(self, index: int) -> bool:
        """Pin an item to prevent automatic sorting.
        
        Args:
            index: Index of item to pin
            
        Returns:
            True if pinned successfully
        """
        async with self._lock:
            if 0 <= index < len(self._queue):
                self._queue[index].is_manual = True
                logger.info(f"Pinned {self._queue[index].song.full_name}")
                return True
            return False
    
    async def unpin_item(self, index: int) -> bool:
        """Unpin an item to allow automatic sorting.
        
        Args:
            index: Index of item to unpin
            
        Returns:
            True if unpinned successfully
        """
        async with self._lock:
            if 0 <= index < len(self._queue):
                self._queue[index].is_manual = False
                logger.info(f"Unpinned {self._queue[index].song.full_name}")
                await self._sort_queue()
                return True
            return False
    
    async def toggle_smart_voting(self, enabled: bool) -> None:
        """Toggle smart voting mode.
        
        Args:
            enabled: Whether to enable smart voting
        """
        async with self._lock:
            self.smart_voting_enabled = enabled
            logger.info(f"Smart voting {'enabled' if enabled else 'disabled'}")
            await self._sort_queue()
    
    def _find_in_queue(self, uri: str) -> Optional[QueueItem]:
        """Find item in queue by URI.
        
        Args:
            uri: Spotify URI to find
            
        Returns:
            QueueItem if found, None otherwise
        """
        return next((item for item in self._queue if item.uri == uri), None)
    
    def _is_on_cooldown(self, uri: str) -> bool:
        """Check if a song is on cooldown.
        
        Args:
            uri: Spotify URI to check
            
        Returns:
            True if on cooldown
        """
        if uri not in self._history:
            return False
        
        last_played = self._history[uri]
        cooldown_seconds = self.rules.song_cooldown_minutes * 60
        
        return (time.time() - last_played) < cooldown_seconds
    
    async def _sort_queue(self) -> None:
        """Sort queue based on current settings."""
        # Separate manual and automatic items
        manual_items = [item for item in self._queue if item.is_manual]
        auto_items = [item for item in self._queue if not item.is_manual]
        
        # Sort automatic items by votes if smart voting enabled
        if self.smart_voting_enabled:
            auto_items.sort(key=lambda x: x.votes, reverse=True)
        
        # Combine: manual items keep their position, auto items sorted
        self._queue = manual_items + auto_items
