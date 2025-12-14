"""Create app icon with Twitch and Spotify colors."""
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 256x256 icon
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Twitch purple and Spotify green
twitch_color = (145, 70, 255)  # Twitch purple
spotify_color = (30, 215, 96)  # Spotify green

# Draw split circle design
# Left half - Twitch purple
draw.pieslice([20, 20, size-20, size-20], 90, 270, fill=twitch_color)
# Right half - Spotify green  
draw.pieslice([20, 20, size-20, size-20], 270, 90, fill=spotify_color)

# Draw white border
draw.ellipse([20, 20, size-20, size-20], outline='white', width=8)

# Draw musical note + chat bubble in center
center_x, center_y = size // 2, size // 2

# Musical note (right side - Spotify)
note_x = center_x + 30
draw.ellipse([note_x-10, center_y+15, note_x+10, center_y+35], fill='white')
draw.rectangle([note_x+8, center_y-25, note_x+18, center_y+20], fill='white')
draw.ellipse([note_x+5, center_y-35, note_x+25, center_y-15], fill='white')

# Chat bubble (left side - Twitch)
chat_x = center_x - 30
draw.rounded_rectangle([chat_x-25, center_y-20, chat_x+15, center_y+15], radius=10, fill='white')
draw.polygon([chat_x-10, center_y+15, chat_x-5, center_y+25, chat_x+5, center_y+15], fill='white')

# Save as ICO
ico_path = 'icon.ico'
img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print(f"✓ Icon created: {ico_path}")

# Also save as PNG for preview
img.save('icon.png')
print(f"✓ Preview created: icon.png")
