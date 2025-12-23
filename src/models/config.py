"""Configuration models using Pydantic for validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class CommandPermission(str, Enum):
    """Permission levels for commands."""
    EVERYONE = "everyone"
    FOLLOWERS = "followers"
    SUBSCRIBERS = "subscribers"
    MODERATORS = "moderators"
    BROADCASTER = "broadcaster"


class TwitchConfig(BaseModel):
    """Twitch connection configuration."""
    
    channel: str = Field(default="", description="Twitch channel name")
    token: str = Field(default="", description="OAuth access token for the bot account")
    client_id: str = Field(default="", description="Twitch App Client ID")
    client_secret: str = Field(default="", description="Twitch App Client Secret")
    
    @field_validator("token")
    @classmethod
    def ensure_oauth_prefix(cls, v: str) -> str:
        """Ensure token starts with 'oauth:' for compatibility."""
        if v and not v.startswith("oauth:"):
            return f"oauth:{v}"
        return v


class SpotifyConfig(BaseModel):
    """Spotify API configuration."""
    
    client_id: str = Field(default="", description="Spotify API Client ID")
    client_secret: str = Field(default="", description="Spotify API Client Secret")
    redirect_uri: str = Field(
        default="http://127.0.0.1:8888/callback",
        description="OAuth redirect URI"
    )
    fallback_playlist_id: Optional[str] = Field(
        default=None,
        description="Autopilot playlist ID for when queue is empty"
    )
    
    @field_validator("fallback_playlist_id")
    @classmethod
    def clean_playlist_id(cls, v: Optional[str]) -> Optional[str]:
        """Extract playlist ID from URL or Spotify URI."""
        if not v:
            return None
        
        if "playlist/" in v:
            try:
                return v.split("playlist/")[1].split("?")[0]
            except IndexError:
                pass
        
        if "spotify:playlist:" in v:
            return v.split(":")[-1]
        
        return v.strip()


class RulesConfig(BaseModel):
    """Queue and song rules configuration."""
    
    max_queue_size: int = Field(default=20, ge=1, description="Maximum songs in queue")
    max_user_requests: int = Field(default=3, ge=1, description="Max concurrent requests per user")
    max_song_length_minutes: int = Field(default=10, ge=1, description="Maximum song length")
    song_cooldown_minutes: int = Field(default=30, ge=0, description="Cooldown before replaying a song")
    user_request_cooldown_minutes: int = Field(default=3, ge=0, description="Cooldown between requests per user (0 = disabled)")


class BlacklistConfig(BaseModel):
    """Blacklist configuration for blocking songs/artists."""
    
    songs: list[str] = Field(default_factory=list, description="Blacklisted song names (case-insensitive partial match)")
    artists: list[str] = Field(default_factory=list, description="Blacklisted artist names (case-insensitive partial match)")


class CommandPermissions(BaseModel):
    """Permission configuration for chat commands."""
    
    sr: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can use !sr command")
    skip: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can use !skip command")
    currentsong: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can use !currentsong/!song command")
    blacklist: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can view !blacklist")
    addblacklist: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can add to blacklist")
    removeblacklist: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can remove from blacklist")
    queue: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can view queue")
    clearqueue: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can clear queue")
    wrongsong: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can remove own last request")
    songinfo: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can view detailed song info")
    srhelp: CommandPermission = Field(default=CommandPermission.EVERYONE, description="Who can view help")
    pauserequests: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can pause song requests")
    resumerequests: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can resume song requests")
    pausesr: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can pause playback")
    resumesr: CommandPermission = Field(default=CommandPermission.MODERATORS, description="Who can resume playback")


class BotConfig(BaseModel):
    """Main bot configuration."""
    
    language: str = Field(default="Deutsch", description="UI language")
    twitch: TwitchConfig = Field(default_factory=TwitchConfig)
    spotify: SpotifyConfig = Field(default_factory=SpotifyConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    blacklist: BlacklistConfig = Field(default_factory=BlacklistConfig)
    command_permissions: CommandPermissions = Field(default_factory=CommandPermissions)
    smart_voting_enabled: bool = Field(default=True, description="Enable vote-based queue sorting")
    requests_paused: bool = Field(default=False, description="Whether song requests are currently paused")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            # Custom encoders if needed
        }
