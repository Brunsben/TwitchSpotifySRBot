"""OBS overlay server for displaying current song."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Set
from aiohttp import web
from aiohttp import WSMsgType

logger = logging.getLogger(__name__)


class OBSOverlayServer:
    """HTTP server for OBS overlay with WebSocket updates."""
    
    def __init__(self, port: int = 8080):
        """Initialize OBS overlay server.
        
        Args:
            port: Port to run server on
        """
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.websockets: Set[web.WebSocketResponse] = set()
        
        # Current song data
        self.current_song = {
            "name": "No song playing",
            "artist": "",
            "cover_url": "",
            "requester": ""
        }
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get('/', self._handle_index)
        self.app.router.add_get('/ws', self._handle_websocket)
        self.app.router.add_get('/api/current', self._handle_api_current)
    
    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serve the overlay HTML page."""
        html = self._get_overlay_html()
        return web.Response(text=html, content_type='text/html')
    
    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for live updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.add(ws)
        logger.info("New WebSocket connection")
        
        # Send current song immediately
        await ws.send_json(self.current_song)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.discard(ws)
            logger.info("WebSocket disconnected")
        
        return ws
    
    async def _handle_api_current(self, request: web.Request) -> web.Response:
        """API endpoint for current song."""
        return web.json_response(self.current_song)
    
    async def start(self):
        """Start the server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', self.port)
        await self.site.start()
        logger.info(f"OBS Overlay server started on http://localhost:{self.port}")
    
    async def stop(self):
        """Stop the server."""
        # Close all websockets
        for ws in self.websockets:
            await ws.close()
        self.websockets.clear()
        
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("OBS Overlay server stopped")
    
    async def update_song(self, name: str, artist: str, cover_url: str = "", requester: str = ""):
        """Update current song and notify all connected clients.
        
        Args:
            name: Song name
            artist: Artist name
            cover_url: URL to album cover image
            requester: Username who requested
        """
        self.current_song = {
            "name": name,
            "artist": artist,
            "cover_url": cover_url,
            "requester": requester
        }
        
        # Broadcast to all connected WebSocket clients
        if self.websockets:
            logger.debug(f"Broadcasting update to {len(self.websockets)} clients")
            disconnected = set()
            
            for ws in self.websockets:
                try:
                    await ws.send_json(self.current_song)
                except Exception as e:
                    logger.error(f"Failed to send to WebSocket: {e}")
                    disconnected.add(ws)
            
            # Remove disconnected clients
            self.websockets -= disconnected
    
    def _get_overlay_html(self) -> str:
        """Generate the overlay HTML page."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Now Playing - Twitch SR Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: transparent;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            align-items: center;
            padding: 20px;
            background: linear-gradient(135deg, #181818 0%, #282828 100%);
            border-radius: 15px;
            border: 2px solid #1DB954;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(29, 185, 84, 0.2);
            max-width: 600px;
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(-100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        
        .cover {
            width: 100px;
            height: 100px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
            margin-right: 20px;
            flex-shrink: 0;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }
        
        .cover img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            animation: fadeIn 0.3s ease-out;
        }
        
        .cover.no-image {
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
        }
        
        .info {
            flex: 1;
            color: white;
            min-width: 0;
        }
        
        .label {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .song-name {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .artist {
            font-size: 18px;
            opacity: 0.95;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .requester {
            font-size: 14px;
            opacity: 0.85;
            font-style: italic;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .hidden {
            display: none;
        }
        
        /* Pulse animation for music note */
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .cover.no-image {
            animation: pulse 2s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container" id="overlay">
        <div class="cover" id="cover">
            <span>🎵</span>
        </div>
        <div class="info">
            <div class="label">NOW PLAYING</div>
            <div class="song-name" id="songName">Waiting for song...</div>
            <div class="artist" id="artist"></div>
            <div class="requester" id="requester"></div>
        </div>
    </div>

    <script>
        let ws;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 10;
        
        function connect() {
            ws = new WebSocket('ws://' + window.location.host + '/ws');
            
            ws.onopen = () => {
                console.log('Connected to server');
                reconnectAttempts = 0;
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateOverlay(data);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = () => {
                console.log('Disconnected from server');
                
                // Attempt to reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
                    setTimeout(connect, delay);
                }
            };
        }
        
        function updateOverlay(data) {
            const overlay = document.getElementById('overlay');
            const cover = document.getElementById('cover');
            const songName = document.getElementById('songName');
            const artist = document.getElementById('artist');
            const requester = document.getElementById('requester');
            
            // Update song info
            songName.textContent = data.name || 'No song playing';
            artist.textContent = data.artist || '';
            
            if (data.requester) {
                requester.textContent = `Requested by: ${data.requester}`;
                requester.classList.remove('hidden');
            } else {
                requester.classList.add('hidden');
            }
            
            // Update cover
            if (data.cover_url) {
                cover.innerHTML = `<img src="${data.cover_url}" alt="Album Cover">`;
                cover.classList.remove('no-image');
            } else {
                cover.innerHTML = '<span>🎵</span>';
                cover.classList.add('no-image');
            }
            
            // Trigger animation
            overlay.style.animation = 'none';
            setTimeout(() => {
                overlay.style.animation = 'slideIn 0.5s ease-out';
            }, 10);
        }
        
        // Start connection
        connect();
    </script>
</body>
</html>"""
