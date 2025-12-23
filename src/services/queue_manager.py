"""Queue manager for handling song queue logic."""
import asyncio
import logging
import time
from typing import List, Optional, Dict
from enum import Enum

from ..models.song import Song, QueueItem
from ..models.config import RulesConfig, BlacklistConfig

logger = logging.getLogger(__name__)


class RequestResult(Enum):
    """Result of a song request."""
    
    SUCCESS = "success"
    QUEUE_FULL = "queue_full"
    USER_LIMIT = "user_limit"
    TOO_LONG = "too_long"
    ON_COOLDOWN = "on_cooldown"
    USER_COOLDOWN = "user_cooldown"
    BLACKLISTED = "blacklisted"
    NOT_FOUND = "not_found"
    VOTED = "voted"
    DUPLICATE = "duplicate"
    REQUESTS_PAUSED = "requests_paused"


class QueueManager:
    """Manages the song queue with voting and rules."""
    
    def __init__(self, rules: RulesConfig, blacklist: BlacklistConfig, smart_voting_enabled: bool = True, requests_paused: bool = False):
        """Initialize queue manager.
        
        Args:
            rules: Queue rules configuration
            blacklist: Blacklist configuration
            smart_voting_enabled: Whether to enable smart voting
            requests_paused: Whether song requests are currently paused
        """
        self.rules = rules
        self.blacklist = blacklist
        self.smart_voting_enabled = smart_voting_enabled
        self.requests_paused = requests_paused
        
        # Log blacklist on init
        logger.info(f"QueueManager initialized with blacklist: {len(blacklist.songs)} songs, {len(blacklist.artists)} artists")
        if blacklist.songs:
            logger.info(f"Blocked songs: {blacklist.songs}")
        if blacklist.artists:
            logger.info(f"Blocked artists: {blacklist.artists}")
        
        self._queue: List[QueueItem] = []
        self._history: Dict[str, float] = {}  # URI -> timestamp
        self._user_cooldowns: Dict[str, float] = {}  # username -> last_request_timestamp
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
    
    def check_user_cooldown(self, username: str) -> bool:
        """Check if user is on cooldown for making requests.
        
        Args:
            username: Username to check
            
        Returns:
            True if user is on cooldown, False otherwise
        """
        if self.rules.user_request_cooldown_minutes == 0:
            return False
        
        if username not in self._user_cooldowns:
            return False
        
        last_request = self._user_cooldowns[username]
        cooldown_seconds = self.rules.user_request_cooldown_minutes * 60
        
        return (time.time() - last_request) < cooldown_seconds
    
    def get_user_cooldown_remaining(self, username: str) -> int:
        """Get remaining cooldown time for user in seconds.
        
        Args:
            username: Username to check
            
        Returns:
            Remaining seconds, 0 if not on cooldown
        """
        if not self.check_user_cooldown(username):
            return 0
        
        last_request = self._user_cooldowns[username]
        cooldown_seconds = self.rules.user_request_cooldown_minutes * 60
        elapsed = time.time() - last_request
        
        return max(0, int(cooldown_seconds - elapsed))
    
    def update_blacklist(self, blacklist: BlacklistConfig) -> None:
        """Update blacklist configuration.
        
        Args:
            blacklist: New blacklist configuration
        """
        self.blacklist = blacklist
        logger.info(f"Blacklist updated: {len(blacklist.songs)} songs, {len(blacklist.artists)} artists")
    
    def check_blacklist(self, song: Song) -> tuple[bool, str]:
        """Check if song or artist is blacklisted.
        
        Args:
            song: Song to check
            
        Returns:
            Tuple of (is_blacklisted, reason) where reason is the matched blacklist entry
        """
        song_name_lower = song.name.lower()
        artist_name_lower = song.artist.lower()
        
        logger.debug(f"Checking blacklist for: '{song.name}' by '{song.artist}'")
        logger.debug(f"Current blacklist - Songs: {self.blacklist.songs}, Artists: {self.blacklist.artists}")
        
        # Check if song name matches any blacklisted song (partial match)
        for blocked_song in self.blacklist.songs:
            if blocked_song.lower() in song_name_lower:
                logger.info(f"Song blocked by blacklist: {song.name} (matches '{blocked_song}')")
                return True, f"Song '{blocked_song}'"
        
        # Check if artist name matches any blacklisted artist (partial match)
        for blocked_artist in self.blacklist.artists:
            if blocked_artist.lower() in artist_name_lower:
                logger.info(f"Song blocked by blacklist: {song.name} by {song.artist} (artist matches '{blocked_artist}')")
                return True, f"Artist '{blocked_artist}'"
        
        return False, ""
    
    async def add_request(self, song: Song, username: str) -> RequestResult:
        """Add a song request to the queue.
        
        Args:
            song: Song to add
            username: Username making the request
            
        Returns:
            RequestResult indicating success or failure reason
        """
        async with self._lock:
            # Check if requests are paused
            if self.requests_paused:
                return RequestResult.REQUESTS_PAUSED
            
            # Check user cooldown (before other checks to prevent spam)
            if self.check_user_cooldown(username):
                return RequestResult.USER_COOLDOWN
            
            # Check blacklist (early check to prevent blacklisted songs)
            is_blacklisted, blacklist_reason = self.check_blacklist(song)
            if is_blacklisted:
                # Store reason in song object for later retrieval
                song._blacklist_reason = blacklist_reason
                return RequestResult.BLACKLISTED
            
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
                # If smart voting is disabled, reject duplicate
                if not self.smart_voting_enabled:
                    return RequestResult.DUPLICATE
                
                # Smart voting: add vote if user hasn't voted yet
                if username not in existing.requesters:
                    existing.votes += 1
                    existing.requesters.append(username)
                    logger.info(f"Vote added for {song.full_name} by {username} ({existing.votes} votes)")
                    # Update user cooldown even for votes
                    self._user_cooldowns[username] = time.time()
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
            
            # Update user cooldown timestamp
            self._user_cooldowns[username] = time.time()
            
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
    
    def remove_track_at_index(self, index: int) -> bool:
        """Remove track at index (sync version for command handlers).
        
        Args:
            index: Index of item to remove
            
        Returns:
            True if removed, False if index invalid
        """
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
    
    def set_requests_paused(self, paused: bool) -> None:
        """Set whether song requests are paused.
        
        Args:
            paused: True to pause requests, False to resume
        """
        self.requests_paused = paused
        status = "paused" if paused else "resumed"
        logger.info(f"Song requests {status}")
    
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
