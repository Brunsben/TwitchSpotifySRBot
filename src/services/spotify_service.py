"""Spotify service for interacting with Spotify API."""
import asyncio
import logging
import random
from typing import Optional, List, Dict
from dataclasses import dataclass

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from ..models.song import Song
from ..models.config import SpotifyConfig

logger = logging.getLogger(__name__)


@dataclass
class PlaybackState:
    """Current Spotify playback state."""
    
    is_playing: bool
    current_track: Optional[Song]
    progress_ms: int
    device_id: Optional[str]


class SpotifyService:
    """Service for managing Spotify playback and searches."""
    
    def __init__(self, config: SpotifyConfig):
        """Initialize Spotify service.
        
        Args:
            config: Spotify configuration
        """
        self.config = config
        self._client: Optional[spotipy.Spotify] = None
        self._device_id: Optional[str] = None
    
    async def connect(self) -> None:
        """Connect to Spotify API."""
        try:
            scope = (
                "user-modify-playback-state "
                "user-read-currently-playing "
                "user-read-playback-state "
                "playlist-read-private "
                "playlist-read-collaborative"
            )
            
            auth = SpotifyOAuth(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                redirect_uri=self.config.redirect_uri,
                scope=scope
            )
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None, 
                lambda: spotipy.Spotify(auth_manager=auth)
            )
            
            await self.refresh_device()
            logger.info("Successfully connected to Spotify")
            
        except Exception as e:
            logger.error(f"Failed to connect to Spotify: {e}")
            raise
    
    async def refresh_device(self) -> None:
        """Refresh active device ID."""
        if not self._client:
            return
        
        try:
            loop = asyncio.get_event_loop()
            devices = await loop.run_in_executor(None, self._client.devices)
            
            if not devices or not devices.get('devices'):
                logger.warning("No Spotify devices found")
                return
            
            # Prefer active device
            for device in devices['devices']:
                if device.get('is_active'):
                    self._device_id = device['id']
                    logger.info(f"Using active device: {device.get('name')}")
                    return
            
            # Use first available device
            self._device_id = devices['devices'][0]['id']
            logger.info(f"Using device: {devices['devices'][0].get('name')}")
            
        except Exception as e:
            logger.error(f"Error refreshing device: {e}")
    
    async def search_track(self, query: str) -> Optional[Song]:
        """Search for a track on Spotify.
        
        Args:
            query: Search query (song name or Spotify URL)
            
        Returns:
            Song object if found, None otherwise
        """
        if not self._client:
            raise RuntimeError("Not connected to Spotify")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Check if it's a Spotify URL or URI
            is_link = "spotify.com/" in query or "spotify:" in query
            
            if is_link:
                # Extract track ID from various URL formats
                # Handles: https://open.spotify.com/track/...
                #          https://open.spotify.com/intl-XX/track/...
                #          spotify:track:...
                if "/track/" in query:
                    track_id = query.split("/track/")[1].split("?")[0]
                    query = f"spotify:track:{track_id}"
                
                logger.debug(f"Fetching track by ID: {query}")
                track = await loop.run_in_executor(
                    None,
                    self._client.track,
                    query
                )
            else:
                # Search by name
                logger.debug(f"Searching for: {query}")
                results = await loop.run_in_executor(
                    None,
                    lambda: self._client.search(q=query, limit=1, type='track')
                )
                
                if not results['tracks']['items']:
                    logger.info(f"No track found for query: {query}")
                    return None
                
                track = results['tracks']['items'][0]
            
            return Song(
                name=track['name'],
                uri=track['uri'],
                duration_ms=track['duration_ms'],
                artist=track['artists'][0]['name']
            )
            
        except Exception as e:
            logger.error(f"Error searching track '{query}': {e}", exc_info=True)
            return None
    
    async def get_playback_state(self) -> Optional[PlaybackState]:
        """Get current playback state.
        
        Returns:
            PlaybackState object if available
        """
        if not self._client:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            current = await loop.run_in_executor(
                None,
                self._client.current_playback
            )
            
            if not current:
                return PlaybackState(
                    is_playing=False,
                    current_track=None,
                    progress_ms=0,
                    device_id=self._device_id
                )
            
            track_item = current.get('item')
            current_track = None
            
            if track_item:
                current_track = Song(
                    name=track_item['name'],
                    uri=track_item['uri'],
                    duration_ms=track_item['duration_ms'],
                    artist=track_item['artists'][0]['name']
                )
            
            return PlaybackState(
                is_playing=current.get('is_playing', False),
                current_track=current_track,
                progress_ms=current.get('progress_ms', 0),
                device_id=current.get('device', {}).get('id')
            )
            
        except Exception as e:
            logger.error(f"Error getting playback state: {e}")
            return None
    
    async def start_playback(self, track_uri: str) -> None:
        """Start playing a track immediately.
        
        Args:
            track_uri: Spotify track URI
        """
        if not self._client or not self._device_id:
            await self.refresh_device()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.start_playback(
                    device_id=self._device_id,
                    uris=[track_uri]
                )
            )
            logger.info(f"Started playback: {track_uri}")
            
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            raise
    
    async def add_to_queue(self, track_uri: str) -> None:
        """Add a track to the queue.
        
        Args:
            track_uri: Spotify track URI
        """
        if not self._client or not self._device_id:
            await self.refresh_device()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.add_to_queue(
                    track_uri,
                    device_id=self._device_id
                )
            )
            logger.debug(f"Added to queue: {track_uri}")
            
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            raise
    
    async def skip_track(self) -> None:
        """Skip current track."""
        if not self._client:
            return
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.next_track(device_id=self._device_id)
            )
            logger.info("Skipped track")
            
        except Exception as e:
            logger.error(f"Error skipping track: {e}")
    
    async def get_random_fallback_track(self) -> Optional[Song]:
        """Get a random track from the fallback playlist.
        
        Returns:
            Random Song from playlist, or None
        """
        if not self.config.fallback_playlist_id or not self._client:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get playlist total count
            playlist_info = await loop.run_in_executor(
                None,
                lambda: self._client.playlist_tracks(
                    self.config.fallback_playlist_id,
                    fields="total",
                    limit=1
                )
            )
            
            total = playlist_info.get('total', 0)
            if total == 0:
                logger.warning("Fallback playlist is empty")
                return None
            
            # Get random track
            offset = random.randint(0, total - 1)
            results = await loop.run_in_executor(
                None,
                lambda: self._client.playlist_items(
                    self.config.fallback_playlist_id,
                    limit=1,
                    offset=offset
                )
            )
            
            if not results['items']:
                return None
            
            track = results['items'][0]['track']
            
            return Song(
                name=track['name'],
                uri=track['uri'],
                duration_ms=track['duration_ms'],
                artist=track['artists'][0]['name']
            )
            
        except Exception as e:
            logger.error(f"Error getting fallback track: {e}")
            return None
    
    async def validate_playlist(self, playlist_id: str) -> bool:
        """Validate that a playlist exists and is accessible.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            True if valid, False otherwise
        """
        if not self._client:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._client.playlist,
                playlist_id
            )
            return True
            
        except Exception as e:
            logger.error(f"Invalid playlist {playlist_id}: {e}")
            return False
