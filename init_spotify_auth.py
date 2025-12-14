"""Initialize Spotify authentication - run this before building the .exe"""
import os
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

# Enter your Spotify credentials here
CLIENT_ID = input("Spotify Client ID: ").strip()
CLIENT_SECRET = input("Spotify Client Secret: ").strip()
REDIRECT_URI = "http://127.0.0.1:8888/callback"

scope = (
    "user-modify-playback-state "
    "user-read-currently-playing "
    "user-read-playback-state "
    "playlist-read-private "
    "playlist-read-collaborative"
)

cache_path = os.path.join(os.path.expanduser("~"), ".spotify_cache")
cache_handler = CacheFileHandler(cache_path=cache_path)

auth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_handler=cache_handler,
    open_browser=True,
    show_dialog=False
)

# This will open browser and save tokens
token_info = auth.get_access_token(as_dict=False)
print(f"\n✓ Authentication successful!")
print(f"✓ Token saved to: {cache_path}")
print(f"\nYou can now build the .exe with: python build.py")

