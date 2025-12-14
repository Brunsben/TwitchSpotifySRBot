"""Build script for creating standalone executable."""
import PyInstaller.__main__
import shutil
from pathlib import Path

# Clean previous builds (ignore errors if files are locked)
try:
    if Path("build").exists():
        shutil.rmtree("build")
except Exception as e:
    print(f"Warning: Could not remove build folder: {e}")

try:
    if Path("dist").exists():
        shutil.rmtree("dist")
except Exception as e:
    print(f"Warning: Could not remove dist folder: {e}")

# Build the executable
PyInstaller.__main__.run([
    'app.py',
    '--name=TwitchSRBot',
    '--onefile',
    '--windowed',  # No console window
    '--icon=icon.ico',  # Custom Twitch+Spotify icon
    '--add-data=icon.ico;.',  # Include icon in exe
    '--add-data=locales;locales',
    '--add-data=src;src',
    '--hidden-import=customtkinter',
    '--hidden-import=spotipy',
    '--hidden-import=twitchio',
    '--hidden-import=requests',
    '--hidden-import=pydantic',
    '--collect-all=customtkinter',
    '--noconsole',
])

print("\n✅ Build complete! Executable is in 'dist' folder.")
print("📦 File: dist/TwitchSRBot.exe")
