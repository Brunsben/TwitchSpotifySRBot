"""Configuration manager for loading and saving settings."""
import json
import logging
from pathlib import Path
from typing import Optional

from ..models.config import BotConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages loading and saving of bot configuration."""
    
    def __init__(self, config_file: Path = Path("config_premium.json")):
        """Initialize the config manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self._config: Optional[BotConfig] = None
    
    def load(self) -> BotConfig:
        """Load configuration from file.
        
        Returns:
            BotConfig instance
        """
        if not self.config_file.exists():
            logger.info("Config file not found, creating default configuration")
            self._config = BotConfig()
            self.save()
            return self._config
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert old format to new format
            converted_data = self._convert_legacy_config(data)
            self._config = BotConfig(**converted_data)
            logger.info("Configuration loaded successfully")
            return self._config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            self._config = BotConfig()
            return self._config
    
    def save(self, config: Optional[BotConfig] = None) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save (uses current if None)
        """
        if config is None:
            config = self._config
        
        if config is None:
            logger.warning("No configuration to save")
            return
        
        try:
            # Convert to dictionary for JSON serialization
            data = self._to_legacy_format(config)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            self._config = config
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    @property
    def config(self) -> BotConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            self.load()
        return self._config
    
    def _convert_legacy_config(self, data: dict) -> dict:
        """Convert old config format to new format.
        
        Args:
            data: Legacy configuration dictionary
            
        Returns:
            New format dictionary
        """
        return {
            "language": data.get("language", "Deutsch"),
            "smart_voting_enabled": True,  # Not stored in old format
            "twitch": {
                "channel": data.get("channel", ""),
                "token": data.get("token", ""),
                "client_id": data.get("twitch_client_id", ""),
                "client_secret": data.get("twitch_client_secret", ""),
            },
            "spotify": {
                "client_id": data.get("sp_id", ""),
                "client_secret": data.get("sp_secret", ""),
                "fallback_playlist_id": data.get("fallback_id"),
            },
            "rules": {
                "max_queue_size": int(data.get("max_queue", 20)),
                "max_user_requests": int(data.get("max_user_reqs", 3)),
                "max_song_length_minutes": int(data.get("max_song_len_min", 10)),
                "song_cooldown_minutes": int(data.get("song_cooldown_min", 30)),
            }
        }
    
    def _to_legacy_format(self, config: BotConfig) -> dict:
        """Convert new config format to legacy format for backwards compatibility.
        
        Args:
            config: BotConfig instance
            
        Returns:
            Legacy format dictionary
        """
        return {
            "language": config.language,
            "channel": config.twitch.channel,
            "token": config.twitch.token.replace("oauth:", "") if config.twitch.token else "",
            "twitch_client_id": config.twitch.client_id,
            "twitch_client_secret": config.twitch.client_secret,
            "sp_id": config.spotify.client_id,
            "sp_secret": config.spotify.client_secret,
            "fallback_id": config.spotify.fallback_playlist_id or "",
            "max_queue": str(config.rules.max_queue_size),
            "max_user_reqs": str(config.rules.max_user_requests),
            "max_song_len_min": str(config.rules.max_song_length_minutes),
            "song_cooldown_min": str(config.rules.song_cooldown_minutes),
        }
