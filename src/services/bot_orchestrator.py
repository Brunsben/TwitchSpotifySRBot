"""Main bot orchestrator coordinating all services."""
import asyncio
import logging
import threading
from typing import Optional, Callable

from ..models.config import BotConfig
from ..models.song import Song, QueueItem
from ..services.spotify_service import SpotifyService, PlaybackState
from ..services.twitch_service import TwitchBotService
from ..services.queue_manager import QueueManager, RequestResult
from ..services.history_manager import HistoryManager
from ..services.obs_overlay import OBSOverlayServer
from ..utils.i18n import t

logger = logging.getLogger(__name__)


class BotOrchestrator:
    """Main bot orchestrator coordinating Spotify, Twitch, and Queue services."""
    
    def __init__(self, config: BotConfig, on_update: Optional[Callable] = None):
        """Initialize bot orchestrator.
        
        Args:
            config: Bot configuration
            on_update: Callback when state changes (for UI updates)
        """
        self.config = config
        self.on_update = on_update
        
        # Services
        self.spotify = SpotifyService(config.spotify)
        self.queue_manager = QueueManager(config.rules, config.smart_voting_enabled)
        self.history_manager = HistoryManager()
        self.obs_overlay = OBSOverlayServer(port=8080)
        self.twitch_bot: Optional[TwitchBotService] = None
        
        # State
        self._running = False
        self._current_track: Optional[QueueItem] = None
        self._playback_loop_task: Optional[asyncio.Task] = None
        self._autopilot_error_count = 0
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
    
    @property
    def is_running(self) -> bool:
        """Check if bot is running."""
        return self._running
    
    @property
    def current_track(self) -> Optional[QueueItem]:
        """Get currently playing track."""
        return self._current_track
    
    async def start(self) -> None:
        """Start the bot."""
        if self._running:
            logger.warning("Bot already running")
            return
        
        try:
            # Store main event loop for thread-safe calls
            self._main_loop = asyncio.get_running_loop()
            
            # Connect to Spotify
            await self.spotify.connect()
            
            # Start OBS overlay server
            await self.obs_overlay.start()
            
            # Start playback loop
            self._running = True
            self._playback_loop_task = asyncio.create_task(self._playback_loop())
            
            # Start Twitch bot in separate thread with proper callback
            self._start_twitch_bot()
            
            logger.info("Bot started successfully")
            self._notify_update()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self._running = False
            raise
    
    def _start_twitch_bot(self):
        """Start Twitch bot in separate thread."""
        def run_bot():
            self.twitch_bot = TwitchBotService(
                self.config.twitch,
                self._handle_song_request_sync,
                self._handle_skip_sync,
                self._handle_current_song_sync
            )
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self.twitch_bot.start_bot())
            except Exception as e:
                logger.error(f"Twitch bot error: {e}")
            finally:
                loop.close()
        
        threading.Thread(target=run_bot, daemon=True).start()
    
    def _handle_song_request_sync(self, query: str, username: str) -> str:
        """Synchronous wrapper for async song request handler.
        
        This is called from Twitch bot's event loop.
        
        Args:
            query: Search query or Spotify link
            username: Username making request
            
        Returns:
            Response message for chat
        """
        if not self._main_loop:
            logger.error("Main event loop not available")
            return t("chat.err_not_found", user=username)
        
        try:
            # Create a future in the main loop where Spotify runs
            future = asyncio.run_coroutine_threadsafe(
                self._handle_song_request(query, username),
                self._main_loop
            )
            # Wait for result (with timeout)
            result = future.result(timeout=15)
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Song request timed out for query: {query}")
            return t("chat.err_not_found", user=username)
        except Exception as e:
            logger.error(f"Error in song request handler:", exc_info=True)
            return t("chat.err_not_found", user=username)
    
    def _handle_skip_sync(self, username: str) -> str:
        """Synchronous wrapper for skip command.
        
        Args:
            username: User who executed the command
        
        Returns:
            Response message for chat
        """
        if not self._main_loop:
            logger.error("Main event loop not available")
            return f"@{username} ⚠️ Fehler beim Überspringen."
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.skip_current(),
                self._main_loop
            )
            future.result(timeout=10)
            
            if self._current_track:
                return f"@{username} ⏭️ Song übersprungen: {self._current_track.song.full_name}"
            return f"@{username} ⏭️ Song übersprungen."
            
        except Exception as e:
            logger.error(f"Error in skip handler:", exc_info=True)
            return f"@{username} ⚠️ Fehler beim Überspringen."
    
    def _handle_current_song_sync(self, username: str) -> str:
        """Synchronous wrapper for current song command.
        
        Args:
            username: User who executed the command
        
        Returns:
            Response message for chat
        """
        if not self._current_track:
            return f"@{username} 🎵 Aktuell läuft kein Song aus der Queue."
        
        track = self._current_track
        requesters = ", ".join(track.requesters[:3])  # Show max 3 requesters
        if len(track.requesters) > 3:
            requesters += f" (+{len(track.requesters) - 3} weitere)"
        
        return f"@{username} 🎵 Aktuell: {track.song.full_name} | Requested by: {requesters}"
    
    async def stop(self) -> None:
        """Stop the bot."""
        if not self._running:
            return
        
        logger.info("Stopping bot orchestrator...")
        self._running = False
        
        # Cancel playback loop
        if self._playback_loop_task:
            self._playback_loop_task.cancel()
            try:
                await self._playback_loop_task
            except asyncio.CancelledError:
                logger.debug("Playback loop cancelled")
        
        # Stop Twitch bot
        if self.twitch_bot:
            try:
                logger.info("Stopping Twitch bot...")
                await self.twitch_bot.close()
                logger.info("Twitch bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Twitch bot: {e}")
        
        # Stop OBS overlay server
        await self.obs_overlay.stop()
        
        logger.info("Bot orchestrator stopped")
        self._notify_update()
    
    async def skip_current(self) -> None:
        """Skip current track."""
        # Mark current track as skipped in history
        if self._current_track:
            requester = self._current_track.requesters[0] if self._current_track.requesters else "Unknown"
            self.history_manager.add_entry(self._current_track.song, requester, was_skipped=True)
        
        await self.spotify.skip_track()
        logger.info("Skipped current track")
    
    async def force_play_next(self) -> None:
        """Force play next track in queue."""
        await self._play_next_song(force_start=True)
    
    async def clear_queue(self) -> None:
        """Clear the queue."""
        await self.queue_manager.clear_queue()
        self._notify_update()
    
    async def toggle_smart_voting(self, enabled: bool) -> None:
        """Toggle smart voting.
        
        Args:
            enabled: Whether to enable smart voting
        """
        await self.queue_manager.toggle_smart_voting(enabled)
        self._notify_update()
    
    async def _handle_song_request(self, query: str, username: str) -> str:
        """Handle song request from Twitch chat.
        
        Args:
            query: Search query or Spotify link
            username: Username making request
            
        Returns:
            Response message for chat
        """
        # Search for song
        song = await self.spotify.search_track(query)
        
        if not song:
            return t("chat.err_not_found", user=username)
        
        # Add to queue
        result = await self.queue_manager.add_request(song, username)
        
        # Generate response based on result
        if result == RequestResult.SUCCESS:
            queue = self.queue_manager.queue
            try:
                idx = next(i for i, item in enumerate(queue) if item.uri == song.uri)
                pos = idx + 1
                wait_ms = sum(item.duration_ms for item in queue[:idx])
                wait_min = int(wait_ms / 60000)
                
                self._notify_update()
                return t("chat.added_pos", user=username, song=song.full_name, pos=pos, wait=wait_min)
            except (StopIteration, ValueError):
                self._notify_update()
                return t("chat.added_simple", user=username, song=song.full_name)
        
        elif result == RequestResult.VOTED:
            # Get updated vote count
            queue = self.queue_manager.queue
            item = next((i for i in queue if i.uri == song.uri), None)
            votes = item.votes if item else 1
            
            self._notify_update()
            return t("chat.voted", user=username, song=song.full_name, votes=votes)
        
        elif result == RequestResult.QUEUE_FULL:
            return t("chat.queue_full", user=username, max=self.config.rules.max_queue_size)
        
        elif result == RequestResult.USER_LIMIT:
            return t("chat.limit_reached", user=username, max=self.config.rules.max_user_requests)
        
        elif result == RequestResult.TOO_LONG:
            return t("chat.err_too_long", user=username, max=self.config.rules.max_song_length_minutes)
        
        elif result == RequestResult.ON_COOLDOWN:
            return t("chat.err_cooldown", user=username)
        
        else:
            return t("chat.err_not_found", user=username)
    
    async def _playback_loop(self) -> None:
        """Main playback loop monitoring Spotify and playing queue."""
        logger.info("Playback loop started")
        
        while self._running:
            try:
                await asyncio.sleep(4)
                
                # Get playback state
                state = await self.spotify.get_playback_state()
                
                if not state:
                    logger.debug("No playback state available")
                    continue
                
                queue = self.queue_manager.queue
                
                logger.debug(f"Playback check - Queue: {len(queue)}, Playing: {state.is_playing}")
                
                # No queue - play fallback if nothing playing
                if not queue:
                    if not state.is_playing:
                        logger.info("Queue empty and nothing playing - starting fallback")
                        await self._play_fallback()
                    else:
                        logger.debug("Queue empty but something is playing")
                    continue
                
                # Queue exists but nothing playing - start playback
                if not state.is_playing:
                    logger.info("Queue has items but nothing playing - starting playback")
                    await self._play_next_song(force_start=True)
                    continue
                
                # Check if current track is ending soon
                if state.current_track:
                    remaining_ms = state.current_track.duration_ms - state.progress_ms
                    
                    # Queue next song when < 10 seconds remaining
                    if remaining_ms < 10000:
                        logger.info(f"Track ending soon ({remaining_ms}ms remaining) - queuing next")
                        await self._play_next_song(force_start=False)
                        await asyncio.sleep(8)  # Wait before next check
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in playback loop: {e}", exc_info=True)
                await asyncio.sleep(5)
        
        logger.info("Playback loop stopped")
    
    async def _play_next_song(self, force_start: bool = False) -> None:
        """Play next song from queue.
        
        Args:
            force_start: If True, start playback immediately; if False, add to Spotify queue
        """
        item = await self.queue_manager.pop_next()
        
        if not item:
            return
        
        self._current_track = item
        self._notify_update()
        
        try:
            if force_start:
                await self.spotify.start_playback(item.uri)
                logger.info(f"Started playback: {item.song.full_name}")
                
                # Track in history
                requester = item.requesters[0] if item.requesters else "Unknown"
                self.history_manager.add_entry(item.song, requester)
                
                # Update OBS overlay
                await self.obs_overlay.update_song(
                    title=item.song.name,
                    artist=item.song.artist,
                    requester=requester,
                    cover_url=item.song.cover_url
                )
            else:
                await self.spotify.add_to_queue(item.uri)
                logger.info(f"Added to Spotify queue: {item.song.full_name}")
        
        except Exception as e:
            logger.error(f"Error playing song: {e}")
    
    async def _play_fallback(self) -> None:
        """Play random track from fallback playlist."""
        if not self.config.spotify.fallback_playlist_id:
            logger.debug("No fallback playlist configured")
            return
        
        if self._autopilot_error_count >= 3:
            logger.warning("Autopilot disabled due to errors")
            return
        
        try:
            logger.info("Attempting to play fallback track")
            song = await self.spotify.get_random_fallback_track()
            
            if not song:
                logger.warning("No fallback track available")
                return
            
            await self.spotify.start_playback(song.uri)
            
            # Set as current track
            self._current_track = QueueItem(
                song=song,
                votes=0,
                requesters=["🤖 Autopilot"],
                is_manual=False
            )
            
            # Track autopilot in history
            self.history_manager.add_entry(song, "Autopilot")
            
            # Update OBS overlay
            await self.obs_overlay.update_song(
                title=song.name,
                artist=song.artist,
                requester="🤖 Autopilot",
                cover_url=song.cover_url
            )
            
            logger.info(f"Playing fallback track: {song.full_name}")
            self._autopilot_error_count = 0
            self._notify_update()
            
            await asyncio.sleep(5)
            
        except Exception as e:
            self._autopilot_error_count += 1
            logger.error(f"Autopilot error ({self._autopilot_error_count}/3): {e}", exc_info=True)
            
            if self._autopilot_error_count >= 3:
                logger.warning("Autopilot disabled due to repeated errors")
            
            await asyncio.sleep(10)
    
    def _notify_update(self) -> None:
        """Notify UI of state change."""
        if self.on_update:
            try:
                self.on_update()
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
