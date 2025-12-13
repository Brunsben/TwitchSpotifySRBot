"""Build script for creating standalone executable."""
import PyInstaller.__main__
import shutil
from pathlib import Path

# Clean previous builds
if Path("build").exists():
    shutil.rmtree("build")
if Path("dist").exists():
    shutil.rmtree("dist")

# Build the executable
PyInstaller.__main__.run([
    'app.py',
    '--name=TwitchSRBot',
    '--onefile',
    '--windowed',  # No console window
    '--icon=NONE',  # Add icon path if you have one
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
