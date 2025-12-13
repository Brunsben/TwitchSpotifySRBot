"""Settings window for configuration."""
import logging
import webbrowser
from typing import Callable
from threading import Thread

import customtkinter as ctk
from tkinter import messagebox

from ..models.config import BotConfig, TwitchConfig, SpotifyConfig, RulesConfig
from ..utils.i18n import t
from ..utils.twitch_oauth import TwitchOAuth

logger = logging.getLogger(__name__)


class SettingsWindow(ctk.CTkToplevel):
    """Settings configuration window."""
    
    def __init__(self, parent, config: BotConfig, on_save: Callable[[BotConfig], None]):
        """Initialize settings window.
        
        Args:
            parent: Parent window
            config: Current configuration
            on_save: Callback when settings are saved
        """
        super().__init__(parent)
        
        self.config = config
        self.on_save_callback = on_save
        
        self.title(t("settings.title"))
        self.geometry("600x750")
        self.attributes("-topmost", True)
        
        # Grid setup
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self, fg_color="#222")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        
        # Create tabs
        tab_rules = self.tabview.add("⚙️ Regeln & Limits")
        tab_twitch = self.tabview.add("🔐 Twitch Login")
        tab_spotify = self.tabview.add("🎵 Spotify API")
        
        # Configure each tab
        self._setup_rules_tab(tab_rules, config)
        self._setup_twitch_tab(tab_twitch, config)
        self._setup_spotify_tab(tab_spotify, config)
        
        # Footer with save button
        footer = ctk.CTkFrame(self, height=80, fg_color="#111")
        footer.grid(row=1, column=0, sticky="ew")
        
        ctk.CTkButton(
            footer,
            text=t("settings.btn_save"),
            fg_color="#1DB954",
            height=45,
            font=("Roboto", 14, "bold"),
            command=self._save_settings
        ).pack(padx=40, pady=15, fill="x")
    
    def _setup_twitch_tab(self, parent, config: BotConfig):
        """Setup Twitch login tab."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Auth Helper Buttons
        ctk.CTkLabel(
            scroll,
            text="Schnellstart",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 10))
        
        auth_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        auth_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        ctk.CTkButton(
            auth_frame,
            text="🔧 Twitch App erstellen",
            fg_color="#9146FF",
            hover_color="#772ce8",
            height=35,
            command=lambda: webbrowser.open("https://dev.twitch.tv/console/apps", new=2, autoraise=False)
        ).pack(side="left", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            auth_frame,
            text="🔑 Token generieren",
            fg_color="#18181b",
            hover_color="#26262c",
            border_width=2,
            border_color="#9146FF",
            height=35,
            command=self._generate_oauth_token
        ).pack(side="left", expand=True, padx=(5, 0))
        
        self._create_divider(scroll)
        
        # Twitch credentials
        self.entry_channel = self._create_input(
            scroll,
            t("settings.lbl_channel"),
            config.twitch.channel
        )
        ctk.CTkLabel(
            scroll,
            text=t("settings.desc_channel"),
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=(0, 10), padx=10)
        
        self.entry_twitch_client_id = self._create_input(
            scroll,
            "Twitch App Client ID",
            config.twitch.client_id
        )
        ctk.CTkLabel(
            scroll,
            text="Von der Twitch Developer Console",
            font=("Arial", 9),
            text_color="#888"
        ).pack(pady=(0, 8), padx=10)
        
        self.entry_twitch_client_secret = self._create_input(
            scroll,
            "Twitch App Client Secret",
            config.twitch.client_secret,
            show="*"
        )
        ctk.CTkLabel(
            scroll,
            text="Von der Twitch Developer Console",
            font=("Arial", 9),
            text_color="#888"
        ).pack(pady=(0, 8), padx=10)
        
        self.entry_token = self._create_input(
            scroll,
            t("settings.lbl_token") + " (Access Token)",
            config.twitch.token.replace("oauth:", "") if config.twitch.token else "",
            show="*"
        )
        ctk.CTkLabel(
            scroll,
            text="User Token mit Scopes: user:read:chat, user:write:chat, user:bot",
            font=("Arial", 9),
            text_color="#e67e22"
        ).pack(pady=(0, 10), padx=10)
    
    def _setup_spotify_tab(self, parent, config: BotConfig):
        """Setup Spotify API tab."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(
            scroll,
            text="Spotify API Credentials",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 5))
        
        # Spotify Developer Dashboard button
        ctk.CTkButton(
            scroll,
            text="🔗 Spotify Developer Dashboard",
            fg_color="#1DB954",
            hover_color="#1ed760",
            height=35,
            command=lambda: webbrowser.open("https://developer.spotify.com/dashboard", new=2, autoraise=False)
        ).pack(pady=(0, 10), padx=10, fill="x")
        
        self.entry_sp_id = self._create_input(
            scroll,
            t("settings.lbl_sp_id"),
            config.spotify.client_id
        )
        
        self.entry_sp_secret = self._create_input(
            scroll,
            t("settings.lbl_sp_secret"),
            config.spotify.client_secret,
            show="*"
        )
        
        self._create_divider(scroll)
        
        ctk.CTkLabel(
            scroll,
            text="Autopilot Playlist",
            font=("Roboto", 14, "bold")
        ).pack(pady=(10, 5))
        
        self.entry_fallback = self._create_input(
            scroll,
            t("settings.lbl_fallback"),
            config.spotify.fallback_playlist_id or ""
        )
        ctk.CTkLabel(
            scroll,
            text=t("settings.desc_fallback"),
            font=("Arial", 10),
            text_color="gray",
            wraplength=400
        ).pack(pady=(0, 10), padx=10)
    
    def _setup_rules_tab(self, parent, config: BotConfig):
        """Setup rules and limits tab."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Language section
        ctk.CTkLabel(
            scroll,
            text="Sprache / Language",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            scroll,
            text=t("settings.lbl_lang"),
            anchor="w",
            font=("Arial", 11),
            text_color="#ccc"
        ).pack(fill="x", padx=10, pady=(5, 2))
        
        self.combo_lang = ctk.CTkComboBox(
            scroll,
            values=["Deutsch", "English"],
            state="readonly",
            width=300
        )
        self.combo_lang.set(config.language)
        self.combo_lang.pack(padx=10, pady=(0, 5))
        
        ctk.CTkLabel(
            scroll,
            text=t("gui.restart_msg"),
            font=("Arial", 9),
            text_color="#888",
            wraplength=400
        ).pack(padx=10, pady=(0, 10))
        
        self._create_divider(scroll)
        
        # Permission section
        ctk.CTkLabel(
            scroll,
            text="Berechtigungen",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            scroll,
            text=t("settings.lbl_permission"),
            font=("Arial", 11, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(5, 5), padx=10)
        
        # Map for permission values to display labels
        self.perm_label_map = {
            "all": t("settings.perm_all"),
            "followers": t("settings.perm_followers"),
            "subscribers": t("settings.perm_subscribers")
        }
        
        # Reverse map for saving
        self.perm_value_map = {v: k for k, v in self.perm_label_map.items()}
        
        self.permission_var = ctk.StringVar(
            value=self.perm_label_map.get(config.twitch.request_permission, self.perm_label_map["all"])
        )
        
        permission_menu = ctk.CTkOptionMenu(
            scroll,
            variable=self.permission_var,
            values=list(self.perm_label_map.values()),
            width=300,
            height=35,
            fg_color="#2b2b2b",
            button_color="#1f538d",
            button_hover_color="#14375e",
            dropdown_fg_color="#2b2b2b",
            dropdown_hover_color="#363636"
        )
        permission_menu.pack(pady=(0, 10), padx=10)
        
        self._create_divider(scroll)
        
        # Queue limits section
        ctk.CTkLabel(
            scroll,
            text="Queue & Song Limits",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 10))
        
        self.entry_max_queue = self._create_input(
            scroll,
            t("settings.lbl_max_q"),
            str(config.rules.max_queue_size)
        )
        
        self.entry_max_user = self._create_input(
            scroll,
            t("settings.lbl_max_user"),
            str(config.rules.max_user_requests)
        )
        
        self.entry_max_len = self._create_input(
            scroll,
            t("settings.lbl_max_len"),
            str(config.rules.max_song_length_minutes)
        )
        
        self.entry_cooldown = self._create_input(
            scroll,
            t("settings.lbl_cooldown"),
            str(config.rules.song_cooldown_minutes)
        )
    
    def _create_section_header(self, parent, text: str):
        """Create section header.
        
        Args:
            parent: Parent widget
            text: Header text
        """
        ctk.CTkLabel(
            parent,
            text=text,
            font=("Roboto", 18, "bold")
        ).pack(pady=(30, 10))
    
    def _create_divider(self, parent):
        """Create horizontal divider.
        
        Args:
            parent: Parent widget
        """
        ctk.CTkFrame(
            parent,
            height=2,
            fg_color="#444"
        ).pack(fill="x", padx=20, pady=10)
    
    def _create_input(self, parent, label: str, value: str, show: str = None) -> ctk.CTkEntry:
        """Create labeled input field.
        
        Args:
            parent: Parent widget
            label: Label text
            value: Initial value
            show: Character to show (for passwords)
            
        Returns:
            CTkEntry widget
        """
        ctk.CTkLabel(
            parent,
            text=label,
            anchor="w",
            font=("Arial", 11),
            text_color="#ccc"
        ).pack(fill="x", padx=10, pady=(5, 2))
        
        entry = ctk.CTkEntry(
            parent,
            show=show,
            fg_color="#333",
            border_color="#555",
            height=32
        )
        entry.insert(0, value)
        entry.pack(fill="x", padx=10, pady=(0, 8))
        
        return entry
    
    def _save_settings(self):
        """Save settings and close window."""
        try:
            # Create new config
            token = self.entry_token.get().strip()
            if token and not token.startswith("oauth:"):
                token = f"oauth:{token}"
            
            # Convert displayed label back to permission value
            selected_label = self.permission_var.get()
            perm_value = self.perm_value_map.get(selected_label, "all")
            
            new_config = BotConfig(
                language=self.combo_lang.get(),
                twitch=TwitchConfig(
                    channel=self.entry_channel.get().strip(),
                    token=token,
                    client_id=self.entry_twitch_client_id.get().strip(),
                    client_secret=self.entry_twitch_client_secret.get().strip(),
                    request_permission=perm_value
                ),
                spotify=SpotifyConfig(
                    client_id=self.entry_sp_id.get().strip(),
                    client_secret=self.entry_sp_secret.get().strip(),
                    fallback_playlist_id=self.entry_fallback.get().strip() or None
                ),
                rules=RulesConfig(
                    max_queue_size=int(self.entry_max_queue.get()),
                    max_user_requests=int(self.entry_max_user.get()),
                    max_song_length_minutes=int(self.entry_max_len.get()),
                    song_cooldown_minutes=int(self.entry_cooldown.get())
                ),
                smart_voting_enabled=self.config.smart_voting_enabled
            )
            
            # Call save callback
            self.on_save_callback(new_config)
            
            logger.info("Settings saved successfully")
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input:\n{e}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")
    
    def _generate_oauth_token(self):
        """Generate OAuth token using Client ID and Secret."""
        client_id = self.entry_twitch_client_id.get().strip()
        client_secret = self.entry_twitch_client_secret.get().strip()
        
        if not client_id or not client_secret:
            messagebox.showwarning(
                "Client ID/Secret fehlt",
                "Bitte erst Client ID und Client Secret eingeben!\n\n"
                "1. Klicke auf 'Twitch App erstellen'\n"
                "2. Erstelle eine App mit Redirect URL: http://localhost:3000/callback\n"
                "3. Kopiere Client ID und Secret hierher\n"
                "4. Dann nochmal auf diesen Button klicken"
            )
            return
        
        messagebox.showinfo(
            "OAuth Flow startet",
            "Dein Browser öffnet sich gleich.\n\n"
            "Bitte autorisiere den Bot mit deinem Twitch-Account.\n"
            "Danach wird der Token automatisch eingetragen."
        )
        
        # Run OAuth flow in separate thread to prevent GUI blocking
        def oauth_thread():
            try:
                oauth = TwitchOAuth(client_id, client_secret)
                token = oauth.get_user_token()
                
                # Update GUI in main thread
                self.after(0, lambda: self._on_oauth_complete(token))
                
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                self.after(0, lambda: messagebox.showerror(
                    "Fehler",
                    f"OAuth Flow fehlgeschlagen:\n{e}"
                ))
        
        Thread(target=oauth_thread, daemon=True).start()
    
    def _on_oauth_complete(self, token: str):
        """Handle OAuth completion in main thread.
        
        Args:
            token: Generated access token or None if failed
        """
        if token:
            self.entry_token.delete(0, "end")
            self.entry_token.insert(0, token)
            messagebox.showinfo(
                "Erfolg!",
                "Token wurde erfolgreich generiert und eingetragen!\n\n"
                "Klicke jetzt auf 'Speichern'."
            )
            logger.info("OAuth token generated successfully")
        else:
            messagebox.showerror(
                "Fehler",
                "Token-Generierung fehlgeschlagen.\n\n"
                "Prüfe die Logs für Details."
            )
