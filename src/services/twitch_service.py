"""Twitch bot service for handling chat commands."""
import asyncio
import logging
from typing import Callable, Optional

import requests
import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from ..models.config import TwitchConfig, CommandPermission
from ..models.config import BotConfig

logger = logging.getLogger(__name__)


class TwitchBotService(commands.Bot):
    """Twitch bot for handling song requests using TwitchIO 3.x EventSub."""
    
    def __init__(
        self,
        config: BotConfig,
        on_song_request: Callable[[str, str], str],
        on_skip: Optional[Callable[[str], str]] = None,
        on_current_song: Optional[Callable[[str], str]] = None,
        on_blacklist: Optional[Callable[[str], str]] = None,
        on_add_blacklist: Optional[Callable[[str, str], str]] = None,
        on_remove_blacklist: Optional[Callable[[str, str], str]] = None,
        on_queue: Optional[Callable[[str], str]] = None,
        on_clear_queue: Optional[Callable[[str], str]] = None,
        on_wrong_song: Optional[Callable[[str], str]] = None,
        on_song_info: Optional[Callable[[str], str]] = None,
        on_srhelp: Optional[Callable[[str], str]] = None,
        on_pause_requests: Optional[Callable[[str], str]] = None,
        on_resume_requests: Optional[Callable[[str], str]] = None,
        on_pause_playback: Optional[Callable[[str], str]] = None,
        on_resume_playback: Optional[Callable[[str], str]] = None
    ):
        """Initialize Twitch bot.
        
        Args:
            config: Full bot configuration (BotConfig with command_permissions)
            on_song_request: Callback for song requests (query, username) -> response message
            on_skip: Callback for skip command (username) -> response message
            on_current_song: Callback for current song command (username) -> response message
            on_blacklist: Callback for blacklist command (username) -> response message
            on_skip: Callback for skip command (username) -> response message
            on_current_song: Callback for current song command (username) -> response message
        """
        # Extract token without oauth: prefix
        token = config.twitch.token
        if token.startswith("oauth:"):
            token = token[6:]
        
        logger.info(f"Initializing TwitchIO 3.x bot for channel: {config.twitch.channel}")
        logger.info(f"Using client_id: {config.twitch.client_id[:10]}...")
        
        # Validate token and get bot_id BEFORE initializing Bot
        # This is required because Bot.__init__() needs bot_id parameter
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Client-Id': config.twitch.client_id
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
            client_id=config.twitch.client_id,
            client_secret=config.twitch.client_secret,
            bot_id=bot_id,  # Required in TwitchIO 3.x
            prefix='!'
        )
        
        # Store instance attributes
        self.prefix = '!'  # Required for command processing
        self.bot_config = config
        self.twitch_config = config.twitch  # Store Twitch config separately for easy access
        self.user_token = token
        self.on_song_request_callback = on_song_request
        self.on_skip_callback = on_skip
        self.on_current_song_callback = on_current_song
        self.on_blacklist_callback = on_blacklist
        self.on_add_blacklist_callback = on_add_blacklist
        self.on_remove_blacklist_callback = on_remove_blacklist
        self.on_queue_callback = on_queue
        self.on_clear_queue_callback = on_clear_queue
        self.on_wrong_song_callback = on_wrong_song
        self.on_song_info_callback = on_song_info
        self.on_srhelp_callback = on_srhelp
        self.on_pause_requests_callback = on_pause_requests
        self.on_resume_requests_callback = on_resume_requests
        self.on_pause_playback_callback = on_pause_playback
        self.on_resume_playback_callback = on_resume_playback
        self._running = False
        self._channel_id = None  # Will be set during setup
        self._follower_cache = {}  # Cache: {user_id: (is_follower, timestamp)}
        self._follower_cache_ttl = 300  # 5 minutes cache
    
    async def setup_hook(self) -> None:
        """Called after login but before ready. Setup EventSub subscriptions here."""
        logger.info("Setting up Twitch bot...")
        
        # Fetch the channel user to get broadcaster_user_id
        try:
            users = await self.fetch_users(logins=[self.bot_config.twitch.channel])
            if not users:
                logger.error(f"Channel '{self.bot_config.twitch.channel}' not found!")
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
        logger.info(f"Channel: {self.bot_config.twitch.channel}")
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
                "Client-Id": self.bot_config.twitch.client_id
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
    
    async def _check_command_permission(self, command_name: str, message) -> tuple[bool, str]:
        """Check if user has permission to use a command.
        
        Args:
            command_name: Name of the command (sr, skip, currentsong, blacklist)
            message: TwitchIO message object
            
        Returns:
            Tuple of (has_permission, error_message_key)
            error_message_key is empty string if permission granted
        """
        # Get required permission level for this command
        command_perms = self.bot_config.command_permissions
        required_perm = getattr(command_perms, command_name, CommandPermission.EVERYONE)
        
        # EVERYONE: Always allowed
        if required_perm == CommandPermission.EVERYONE:
            return True, ""
        
        # Get user info
        chatter_name = message.chatter.name
        chatter = message.chatter
        
        # Get badges (broadcaster, moderator, subscriber, vip)
        badges = {}
        if hasattr(chatter, 'badges'):
            badges = {badge.set_id: badge.id for badge in chatter.badges}
        
        # BROADCASTER: Only broadcaster
        if required_perm == CommandPermission.BROADCASTER:
            if "broadcaster" in badges:
                return True, ""
            return False, "err_cmd_perm_broadcaster"
        
        # MODERATORS: Broadcaster or Moderator
        if required_perm == CommandPermission.MODERATORS:
            if "broadcaster" in badges or "moderator" in badges:
                return True, ""
            return False, "err_cmd_perm_moderators"
        
        # SUBSCRIBERS: Broadcaster, Moderator, or Subscriber
        if required_perm == CommandPermission.SUBSCRIBERS:
            if "broadcaster" in badges or "moderator" in badges or "subscriber" in badges:
                return True, ""
            return False, "err_cmd_perm_subscribers"
        
        # FOLLOWERS: Check follower status
        if required_perm == CommandPermission.FOLLOWERS:
            if "broadcaster" in badges or "moderator" in badges or "subscriber" in badges:
                return True, ""
            
            # Check follower status via API
            try:
                user_id = chatter.id
                is_follower = await self._check_follower_status(chatter_name, user_id)
                if is_follower:
                    return True, ""
                else:
                    return False, "err_cmd_perm_followers"
            except Exception as e:
                logger.error(f"Error checking follower status for {chatter_name}: {e}")
                # On error, be lenient
                return True, ""
        
        # Default: Allow
        return True, ""
    
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
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('sr', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
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
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('skip', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
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
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('currentsong', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_current_song_callback:
                try:
                    response = self.on_current_song_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in current song handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Abrufen des aktuellen Songs.")
            else:
                await message.respond(f"@{username} Aktuelle Song-Funktion nicht verfügbar.")
        
        elif command_name == 'blacklist':
            username = chatter_name
            logger.info(f"!blacklist command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('blacklist', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_blacklist_callback:
                try:
                    response = self.on_blacklist_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in blacklist handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Abrufen der Blacklist.")
            else:
                await message.respond(f"@{username} Blacklist-Funktion nicht verfügbar.")
        
        elif command_name == 'addblacklist':
            username = chatter_name
            entry = parts[1] if len(parts) > 1 else ''
            logger.info(f"!addblacklist command from {username}: '{entry}'")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('addblacklist', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if not entry:
                await message.respond(f"@{username} Bitte gib einen Song oder Artist an.")
                return
            
            if self.on_add_blacklist_callback:
                try:
                    response = self.on_add_blacklist_callback(username, entry)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in addblacklist handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Hinzufügen zur Blacklist.")
            else:
                await message.respond(f"@{username} Blacklist-Funktion nicht verfügbar.")
        
        elif command_name == 'removeblacklist':
            username = chatter_name
            entry = parts[1] if len(parts) > 1 else ''
            logger.info(f"!removeblacklist command from {username}: '{entry}'")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('removeblacklist', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if not entry:
                await message.respond(f"@{username} Bitte gib einen Song oder Artist an.")
                return
            
            if self.on_remove_blacklist_callback:
                try:
                    response = self.on_remove_blacklist_callback(username, entry)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in removeblacklist handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Entfernen von der Blacklist.")
            else:
                await message.respond(f"@{username} Blacklist-Funktion nicht verfügbar.")
        
        elif command_name == 'queue':
            username = chatter_name
            logger.info(f"!queue command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('queue', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_queue_callback:
                try:
                    response = self.on_queue_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in queue handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Abrufen der Queue.")
            else:
                await message.respond(f"@{username} Queue-Funktion nicht verfügbar.")
        
        elif command_name == 'clearqueue':
            username = chatter_name
            logger.info(f"!clearqueue command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('clearqueue', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_clear_queue_callback:
                try:
                    response = self.on_clear_queue_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in clearqueue handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Leeren der Queue.")
            else:
                await message.respond(f"@{username} Queue-Funktion nicht verfügbar.")
        
        elif command_name == 'songinfo':
            username = chatter_name
            logger.info(f"!songinfo command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('songinfo', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_song_info_callback:
                try:
                    response = self.on_song_info_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in songinfo handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Abrufen der Song-Informationen.")
            else:
                await message.respond(f"@{username} Funktion nicht verfügbar.")
        
        elif command_name == 'wrongsong' or command_name == 'oops':
            username = chatter_name
            logger.info(f"!wrongsong command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('wrongsong', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_wrong_song_callback:
                try:
                    response = self.on_wrong_song_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in wrongsong handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Entfernen.")
            else:
                await message.respond(f"@{username} Funktion nicht verfügbar.")
        
        elif command_name == 'pauserequests':
            username = chatter_name
            logger.info(f"!pauserequests command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('pauserequests', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_pause_requests_callback:
                try:
                    response = self.on_pause_requests_callback(username)
                    if response:
                        await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in pauserequests handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Pausieren der Requests.")
            else:
                await message.respond(f"@{username} Funktion nicht verfügbar.")
        
        elif command_name == 'resumerequests':
            username = chatter_name
            logger.info(f"!resumerequests command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('resumerequests', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_resume_requests_callback:
                try:
                    response = self.on_resume_requests_callback(username)
                    if response:
                        await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in resumerequests handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Fortsetzen der Requests.")
            else:
                await message.respond(f"@{username} Funktion nicht verfügbar.")
        
        elif command_name == 'pausesr':
            username = chatter_name
            logger.info(f"!pausesr command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('pausesr', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_pause_playback_callback:
                try:
                    response = self.on_pause_playback_callback(username)
                    if response:
                        await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in pausesr handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Pausieren.")
            else:
                await message.respond(f"@{username} Funktion nicht verfügbar.")
        
        elif command_name == 'resumesr':
            username = chatter_name
            logger.info(f"!resumesr command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('resumesr', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_resume_playback_callback:
                try:
                    response = self.on_resume_playback_callback(username)
                    if response:
                        await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in resumesr handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Fortsetzen.")
            else:
                await message.respond(f"@{username} Funktion nicht verfügbar.")
        
        elif command_name == 'srhelp' or command_name == 'commands':
            username = chatter_name
            logger.info(f"!srhelp command from {username}")
            
            # Check command permission
            has_perm, error_key = await self._check_command_permission('srhelp', message)
            if not has_perm:
                error_msg = self.i18n.get(error_key, user=username)
                await message.respond(error_msg)
                return
            
            if self.on_srhelp_callback:
                try:
                    response = self.on_srhelp_callback(username)
                    await message.respond(response)
                except Exception as e:
                    logger.error(f"Error in srhelp handler:", exc_info=True)
                    await message.respond(f"@{username} Fehler beim Abrufen der Hilfe.")
            else:
                await message.respond(f"@{username} Hilfe nicht verfügbar.")
    
    async def _handle_pause_requests(self, message) -> None:
        """Handle !pauserequests command."""
        username = message.chatter.name
        logger.info(f"!pauserequests command from {username}")
        
        # Check permissions
        allowed, error_key = await self._check_command_permission(message, "pauserequests")
        if not allowed:
            await message.respond(t(error_key, user=username))
            return
        
        # Call callback
        if self.on_pause_requests_callback:
            response = self.on_pause_requests_callback(username)
            if response:
                await message.respond(response)
        else:
            await message.respond(f"@{username} Funktion nicht verfügbar.")
    
    async def _handle_resume_requests(self, message) -> None:
        """Handle !resumerequests command."""
        username = message.chatter.name
        logger.info(f"!resumerequests command from {username}")
        
        # Check permissions
        allowed, error_key = await self._check_command_permission(message, "resumerequests")
        if not allowed:
            await message.respond(t(error_key, user=username))
            return
        
        # Call callback
        if self.on_resume_requests_callback:
            response = self.on_resume_requests_callback(username)
            if response:
                await message.respond(response)
        else:
            await message.respond(f"@{username} Funktion nicht verfügbar.")
    
    async def start_bot(self) -> None:
        """Start the Twitch bot."""
        try:
            logger.info(f"Starting Twitch bot for channel: {self.twitch_config.channel}")
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
