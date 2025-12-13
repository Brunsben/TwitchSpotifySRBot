"""Configuration models using Pydantic for validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class TwitchConfig(BaseModel):
    """Twitch connection configuration."""
    
    channel: str = Field(default="", description="Twitch channel name")
    token: str = Field(default="", description="OAuth access token for the bot account")
    client_id: str = Field(default="", description="Twitch App Client ID")
    client_secret: str = Field(default="", description="Twitch App Client Secret")
    request_permission: str = Field(
        default="all",
        description="Who can make song requests: 'all', 'followers', 'subscribers'"
    )
    
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


class BotConfig(BaseModel):
    """Main bot configuration."""
    
    language: str = Field(default="Deutsch", description="UI language")
    twitch: TwitchConfig = Field(default_factory=TwitchConfig)
    spotify: SpotifyConfig = Field(default_factory=SpotifyConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    smart_voting_enabled: bool = Field(default=True, description="Enable vote-based queue sorting")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            # Custom encoders if needed
        }
