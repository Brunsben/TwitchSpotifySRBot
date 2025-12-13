"""Twitch OAuth2 helper for user token generation."""
import logging
import webbrowser
import http.server
import socketserver
import urllib.parse
from threading import Thread
from typing import Optional

logger = logging.getLogger(__name__)


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    auth_code = None
    
    def do_GET(self):
        """Handle GET request with OAuth code."""
        logger.debug(f"Received callback: {self.path}")
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        logger.debug(f"Query params: {params}")
        
        if 'code' in params:
            OAuthCallbackHandler.auth_code = params['code'][0]
            logger.info(f"Authorization code received: {OAuthCallbackHandler.auth_code[:10]}...")
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
                <html>
                <head><title>Twitch Auth Success</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #9146FF;">Erfolgreich!</h1>
                    <p>Du kannst dieses Fenster jetzt schließen.</p>
                    <p>Der Bot wurde autorisiert.</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
        elif 'error' in params:
            error = params['error'][0]
            error_desc = params.get('error_description', ['Unknown error'])[0]
            logger.error(f"OAuth error: {error} - {error_desc}")
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Fehler!</h1>
                    <p>OAuth Fehler: {error}</p>
                    <p>{error_desc}</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            logger.warning("No code or error in callback")
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Fehler!</h1>
                    <p>Keine Autorisierung erhalten.</p>
                    <p>Stelle sicher, dass die Redirect URI in deiner Twitch App auf<br><strong>http://localhost:3000/callback</strong> gesetzt ist!</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class TwitchOAuth:
    """Twitch OAuth2 helper."""
    
    REDIRECT_URI = "http://localhost:3000/callback"
    # Updated scopes for TwitchIO 3.x EventSub
    # user:read:chat - Required for receiving chat messages via EventSub
    # user:write:chat - Required for sending chat messages
    # user:bot - Indicates this is a bot account
    SCOPES = ["user:read:chat", "user:write:chat", "user:bot"]
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize OAuth helper.
        
        Args:
            client_id: Twitch app client ID
            client_secret: Twitch app client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_user_token(self) -> Optional[str]:
        """Start OAuth flow and get user access token.
        
        Returns:
            User access token or None if failed
        """
        # Build authorization URL
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': self.REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES)
        }
        auth_url = f"https://id.twitch.tv/oauth2/authorize?{urllib.parse.urlencode(auth_params)}"
        
        logger.info("Starting OAuth2 flow...")
        logger.info(f"Redirect URI: {self.REDIRECT_URI}")
        logger.info(f"Scopes: {', '.join(self.SCOPES)}")
        logger.info(f"Opening browser for authorization...")
        
        # Start local server for callback
        OAuthCallbackHandler.auth_code = None
        try:
            server = socketserver.TCPServer(("", 3000), OAuthCallbackHandler)
            logger.info("OAuth callback server started on port 3000")
        except OSError as e:
            logger.error(f"Failed to start server on port 3000: {e}")
            logger.error("Port might be in use. Close other applications using port 3000.")
            return None
        
        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()
        
        # Open browser in background (new=2 = new tab, autoraise=False = don't steal focus)
        webbrowser.open(auth_url, new=2, autoraise=False)
        
        # Wait for callback
        logger.info("Waiting for authorization... (timeout: 120s)")
        server_thread.join(timeout=120)  # 2 minutes timeout
        
        server.server_close()
        
        if not OAuthCallbackHandler.auth_code:
            logger.error("No authorization code received")
            logger.error("Make sure the Redirect URI in your Twitch App is set to: http://localhost:3000/callback")
            return None
        
        # Exchange code for token
        logger.info("Exchanging code for access token...")
        import requests
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': OAuthCallbackHandler.auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.REDIRECT_URI
        }
        
        try:
            response = requests.post('https://id.twitch.tv/oauth2/token', data=token_data)
            response.raise_for_status()
            token_info = response.json()
            
            access_token = token_info.get('access_token')
            if access_token:
                logger.info("✓ Successfully obtained user access token!")
                return access_token
            else:
                logger.error("No access token in response")
                return None
                
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None
