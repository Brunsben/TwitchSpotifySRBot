"""Twitch bot service for handling chat commands."""
import asyncio
import logging
from typing import Callable, Optional

import requests
import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from ..models.config import TwitchConfig

logger = logging.getLogger(__name__)


class TwitchBotService(commands.Bot):
    """Twitch bot for handling song requests using TwitchIO 3.x EventSub."""
    
    def __init__(
        self,
        config: TwitchConfig,
        on_song_request: Callable[[str, str], str],
        on_skip: Optional[Callable[[str], str]] = None,
        on_current_song: Optional[Callable[[str], str]] = None
    ):
        """Initialize Twitch bot.
        
        Args:
            config: Twitch configuration
            on_song_request: Callback for song requests (query, username) -> response message
            on_skip: Callback for skip command (username) -> response message
            on_current_song: Callback for current song command (username) -> response message
        """
        # Extract token without oauth: prefix
        token = config.token
        if token.startswith("oauth:"):
            token = token[6:]
        
        logger.info(f"Initializing TwitchIO 3.x bot for channel: {config.channel}")
        logger.info(f"Using client_id: {config.client_id[:10]}...")
        
        # Validate token and get bot_id BEFORE initializing Bot
        # This is required because Bot.__init__() needs bot_id parameter
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Client-Id': config.client_id
            }
            response = requests.get('https://id.twitch.tv/oauth2/validate', headers=headers)
            response.raise_for_status()
            token_info = response.json()
            bot_id = token_info['user_id']
            logger.info(f"Bot user ID: {bot_id} (validated)")
        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
            raise
        
        # Initialize Bot (extends Client)
        # In TwitchIO 3.x, Bot requires bot_id parameter
        super().__init__(
            client_id=config.client_id,
            client_secret=config.client_secret,
            bot_id=bot_id,  # Required in TwitchIO 3.x
            prefix='!'
        )
        
        # Store instance attributes
        self.prefix = '!'  # Required for command processing
        self.bot_config = config
        self.user_token = token
        self.on_song_request_callback = on_song_request
        self.on_skip_callback = on_skip
        self.on_current_song_callback = on_current_song
        self._running = False
        self._channel_id = None  # Will be set during setup
        self._follower_cache = {}  # Cache: {user_id: (is_follower, timestamp)}
        self._follower_cache_ttl = 300  # 5 minutes cache
    
    async def setup_hook(self) -> None:
        """Called after login but before ready. Setup EventSub subscriptions here."""
        logger.info("Setting up Twitch bot...")
        
        # Fetch the channel user to get broadcaster_user_id
        try:
            users = await self.fetch_users(logins=[self.bot_config.channel])
            if not users:
                logger.error(f"Channel '{self.bot_config.channel}' not found!")
                return
            
            broadcaster = users[0]
            self._channel_id = broadcaster.id
            logger.info(f"Found channel: {broadcaster.name} (ID: {self._channel_id})")
            
            # Add token to TwitchIO's management (use empty refresh since we don't have one)
            await self.add_token(self.user_token, refresh="")
            logger.info("User token added to TwitchIO")
            
            # Subscribe to chat messages via EventSub (this is how TwitchIO 3.x works!)
            chat_subscription = eventsub.ChatMessageSubscription(
                broadcaster_user_id=self._channel_id,
                user_id=self.bot_id  # Bot account ID (already set in __init__)
            )
            
            logger.info(f"Subscribing to chat messages for channel {self._channel_id}...")
            response = await self.subscribe_websocket(
                payload=chat_subscription,
                token_for=self.bot_id  # Use bot's user token
            )
            
            if response:
                # Response is a dict in TwitchIO 3.x
                sub_id = response.get('id', 'unknown') if isinstance(response, dict) else getattr(response, 'id', 'unknown')
                logger.info(f"✓ Subscribed to chat messages! Subscription ID: {sub_id}")
            else:
                logger.error("Failed to subscribe to chat messages!")
                
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}", exc_info=True)
    
    async def event_ready(self):
        """Called when bot is ready."""
        logger.info(f"✓✓✓ Twitch bot is READY!")
        logger.info(f"Channel: {self.bot_config.channel}")
        logger.info(f"Listening for chat messages via EventSub...")
        self._running = True
    
    async def event_channel_joined(self, channel):
        """Called when the bot joins a channel."""
        logger.info(f"✓✓✓ Bot successfully joined channel: {channel.name}")
        logger.info("Ready to receive messages!")
    
    async def event_error(self, error, data=None):
        """Called when an error occurs."""
        logger.error(f"Twitch error: {error}")
        if hasattr(error, 'error'):
            logger.error(f"Error detail: {error.error}")
        if hasattr(error, 'original'):
            logger.error(f"Original message: {error.original}")
        if data:
            logger.error(f"Error data: {data}")
    
    async def _check_permissions(self, message) -> Optional[str]:
        """Check if user has permission to make song requests.
        
        Args:
            message: ChatMessage object
            
        Returns:
            Error message if no permission, None if allowed
        """
        permission_level = self.bot_config.request_permission
        
        # Everyone allowed
        if permission_level == "all":
            return None
        
        # Check badges
        badges = {badge.set_id for badge in message.badges} if message.badges else set()
        username = message.chatter.name
        
        # Broadcaster and moderators always allowed
        if "broadcaster" in badges or "moderator" in badges:
            return None
        
        # Check for subscriber requirement
        if permission_level == "subscribers":
            # Check for any subscriber badge
            subscriber_badges = {"subscriber", "founder", "vip"}
            if not badges.intersection(subscriber_badges):
                from ..utils.i18n import t
                return t("chat.err_no_permission", user=username, requirement="Subscriber")
        
        # Check for follower requirement
        elif permission_level == "followers":
            # Subscribers/VIPs are always allowed (they're loyal supporters)
            subscriber_badges = {"subscriber", "founder", "vip"}
            if badges.intersection(subscriber_badges):
                return None
            
            # Check if user is a follower via API
            user_id = message.chatter.id
            is_follower = await self._check_follower_status(user_id, username)
            
            if not is_follower:
                from ..utils.i18n import t
                return t("chat.err_no_permission", user=username, requirement="Follower")
        
        return None
    
    async def _check_follower_status(self, user_id: str, username: str) -> bool:
        """Check if user is a follower via Twitch API.
        
        Args:
            user_id: Twitch user ID
            username: Username (for logging)
            
        Returns:
            True if user is a follower, False otherwise
        """
        import time
        
        # Check cache first
        if user_id in self._follower_cache:
            is_follower, timestamp = self._follower_cache[user_id]
            # Cache valid for 5 minutes
            if time.time() - timestamp < self._follower_cache_ttl:
                logger.debug(f"Follower status for {username} from cache: {is_follower}")
                return is_follower
        
        # Make API call
        try:
            url = "https://api.twitch.tv/helix/channels/followers"
            params = {
                "broadcaster_id": self._channel_id,
                "user_id": user_id
            }
            headers = {
                "Authorization": f"Bearer {self.user_token.replace('oauth:', '')}",
                "Client-Id": self.bot_config.client_id
            }
            
            logger.debug(f"Checking follower status for {username} (ID: {user_id})")
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, params=params, headers=headers, timeout=5)
            )
            
            if response.status_code == 200:
                data = response.json()
                is_follower = len(data.get('data', [])) > 0
                
                # Cache result
                self._follower_cache[user_id] = (is_follower, time.time())
                
                logger.info(f"Follower check for {username}: {is_follower}")
                return is_follower
            else:
                logger.error(f"Follower check API error: {response.status_code} - {response.text}")
                # On error, be lenient and allow
                return True
                
        except Exception as e:
            logger.error(f"Error checking follower status for {username}: {e}")
            # On error, be lenient and allow
            return True
    
    async def event_message(self, message) -> None:
        """Handle chat messages from EventSub.
        
        In TwitchIO 3.x, EventSub messages are dispatched as event_message.
        The message is a ChatMessage object from twitchio.models.eventsub_.
        """
        # Extract data from ChatMessage object
        try:
            chatter_name = message.chatter.name
            message_text = message.text  # Direct .text attribute in EventSub ChatMessage
            broadcaster_id = message.broadcaster.id
        except AttributeError as e:
            # Log the actual structure for debugging
            logger.error(f"AttributeError accessing message: {e}")
            logger.debug(f"Message type: {type(message)}")
            logger.debug(f"Message dir: {dir(message)}")
            return
        
        logger.info(f"[CHAT] {chatter_name}: {message_text}")
        
        # Check if message starts with our prefix
        if not message_text.startswith(self.prefix):
            return
        
        # Parse command
        parts = message_text[len(self.prefix):].split(' ', 1)
        command_name = parts[0].lower()
        
        if command_name == 'sr':
            query = parts[1] if len(parts) > 1 else ''
            username = chatter_name
            
            logger.info(f"!sr command from {username}: '{query}'")
            
            # Check permissions
            permission_result = await self._check_permissions(message)
            if permission_result:
                await message.respond(permission_result)
                return
            
            if not query:
                # Respond using EventSub ChatMessage.respond() method
                await message.respond(f"@{username} Bitte gib einen Songnamen oder Link an.")
                return
            
            try:
                # Call the sync callback
                logger.debug(f"Calling on_song_request_callback with query='{query}', username='{username}'")
                response = self.on_song_request_callback(query, username)
                logger.debug(f"Callback response: {response}")
                
                # Send response using EventSub ChatMessage.respond() method
                await message.respond(response)
                logger.info(f"Sent response to {username}")
                
            except Exception as e:
                logger.error(f"Error in song request handler:", exc_info=True)
                await message.respond(f"@{username} Ein Fehler ist aufgetreten.")
        
        elif command_name == 'skip':
            username = chatter_name
            logger.info(f"!skip command from {username}")
            
            # Check if user is broadcaster or moderator
            badges = {badge.set_id for badge in message.badges} if message.badges else set()
            if "broadcaster" not in badges and "moderator" not in badges:
                await message.respond(f"@{username} Nur Broadcaster und Moderatoren können Songs überspringen.")
                return
            
            if self.on_skip_callback:
                try:
                    response = self.on_skip_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in skip handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Überspringen.")
            else:
                await message.respond(f"@{username} Skip-Funktion nicht verfügbar.")
        
        elif command_name == 'currentsong' or command_name == 'song':
            username = chatter_name
            logger.info(f"!{command_name} command from {username}")
            
            if self.on_current_song_callback:
                try:
                    response = self.on_current_song_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in current song handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Abrufen des aktuellen Songs.")
            else:
                await message.respond(f"@{username} Aktuelle Song-Funktion nicht verfügbar.")
    
    async def start_bot(self) -> None:
        """Start the Twitch bot."""
        try:
            logger.info(f"Starting Twitch bot for channel: {self.bot_config.channel}")
            await self.start()
        except Exception as e:
            logger.error(f"Error starting Twitch bot: {e}")
            raise
    
    async def stop_bot(self) -> None:
        """Stop the Twitch bot."""
        self._running = False
        try:
            await self.close()
            logger.info("Twitch bot stopped")
        except Exception as e:
            logger.error(f"Error stopping Twitch bot: {e}")
