"""Main GUI application."""
import asyncio
import logging
import sys
import math
import webbrowser
import threading
from pathlib import Path
from typing import Optional
from tkinter import messagebox

import customtkinter as ctk

from ..models.config import BotConfig
from ..services.bot_orchestrator import BotOrchestrator
from ..utils.config_manager import ConfigManager
from ..utils.i18n import get_i18n, t
from ..utils.logging_config import GUILogHandler

logger = logging.getLogger(__name__)


class BotGUI(ctk.CTk):
    """Main GUI application for the Twitch Spotify Bot."""
    
    # Colors
    COLOR_BG = "#121212"
    COLOR_PANEL = "#181818"
    COLOR_CARD = "#282828"
    COLOR_SPOTIFY = "#1DB954"
    COLOR_RED = "#e74c3c"
    
    def __init__(self):
        """Initialize the GUI."""
        super().__init__()
        
        # Configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        
        # Load language
        i18n = get_i18n()
        lang_code = "de" if self.config.language == "Deutsch" else "en"
        i18n.load_language(lang_code)
        
        # Setup theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")
        
        # Setup window
        self.title(t("gui.title"))
        self.geometry("1200x900")
        self.configure(fg_color=self.COLOR_BG)
        
        # Set icon for taskbar and window
        try:
            import sys
            import os
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_path = sys._MEIPASS
            else:
                # Running as script
                base_path = Path(__file__).parent.parent.parent
            
            icon_path = Path(base_path) / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception as e:
            logger.warning(f"Could not set icon: {e}")
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Bot orchestrator
        self.bot: Optional[BotOrchestrator] = None
        self.smart_voting_var = ctk.BooleanVar(value=self.config.smart_voting_enabled)
        
        # Event loop for async operations (runs in background thread)
        self.loop = None
        self.loop_thread = None
        self._start_event_loop()
        
        # GUI components
        self._setup_layout()
        self._setup_sidebar()
        self._setup_main_area()
        self._setup_control_bar()
        
        # Add GUI log handler
        gui_handler = GUILogHandler(self._log_to_gui)
        logging.getLogger().addHandler(gui_handler)
        
        logger.info("GUI initialized")
    
    def _start_event_loop(self):
        """Start event loop in background thread."""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # Wait for loop to start
        import time
        time.sleep(0.1)
    
    def _setup_layout(self):
        """Setup main layout grid."""
        self.grid_columnconfigure(0, weight=0, minsize=320)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _setup_sidebar(self):
        """Setup sidebar with controls."""
        self.frame_side = ctk.CTkFrame(
            self,
            width=320,
            corner_radius=0,
            fg_color=self.COLOR_PANEL
        )
        self.frame_side.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Logo
        ctk.CTkLabel(
            self.frame_side,
            text="TWITCH\nSR BOT",
            font=("Roboto", 22, "bold"),
            text_color="white",
            justify="center"
        ).pack(pady=(40, 5))
        
        # Status
        self.status_lbl = ctk.CTkLabel(
            self.frame_side,
            text=t("gui.status_offline"),
            text_color="#7f8c8d",
            font=("Roboto", 14, "bold")
        )
        self.status_lbl.pack(pady=(0, 20))
        
        # Smart voting switch
        self.switch_smart = ctk.CTkSwitch(
            self.frame_side,
            text=t("gui.switch_smart"),
            variable=self.smart_voting_var,
            command=self._on_smart_voting_toggle,
            font=("Roboto", 14),
            progress_color=self.COLOR_SPOTIFY
        )
        self.switch_smart.pack(pady=20, padx=40, anchor="w")
        
        # Settings button
        ctk.CTkButton(
            self.frame_side,
            text=t("gui.btn_settings"),
            fg_color="#333",
            hover_color="#444",
            font=("Roboto", 14),
            height=40,
            command=self._open_settings
        ).pack(fill="x", padx=30, pady=10)
        
        # Help button
        ctk.CTkButton(
            self.frame_side,
            text=t("gui.btn_help"),
            fg_color="#333",
            hover_color="#444",
            font=("Roboto", 14),
            height=40,
            command=self._open_help
        ).pack(fill="x", padx=30, pady=10)
        
        # Debug toggle button
        self.debug_visible = False
        self.btn_debug = ctk.CTkButton(
            self.frame_side,
            text="🔍 Debug Log",
            fg_color="#222",
            hover_color="#333",
            font=("Roboto", 12),
            height=35,
            command=self._toggle_debug
        )
        self.btn_debug.pack(fill="x", padx=30, pady=(50, 10))
        
        # Spacer
        ctk.CTkLabel(self.frame_side, text="").pack(expand=True)
        
        # Start/Stop button
        self.btn_start = ctk.CTkButton(
            self.frame_side,
            text=t("gui.btn_start"),
            fg_color=self.COLOR_SPOTIFY,
            hover_color="#1ed760",
            height=60,
            font=("Roboto", 18, "bold"),
            corner_radius=30,
            command=self._toggle_bot
        )
        self.btn_start.pack(fill="x", padx=30, pady=(40, 20))
        
        # Credits
        ctk.CTkLabel(
            self.frame_side,
            text=t("gui.credits"),
            text_color="#555",
            font=("Arial", 10)
        ).pack(side="bottom", pady=10)
    
    def _setup_main_area(self):
        """Setup main content area."""
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.frame_main.grid_rowconfigure(2, weight=1)
        self.frame_main.grid_columnconfigure(0, weight=1)
        
        # Now Playing section
        frame_np = ctk.CTkFrame(
            self.frame_main,
            fg_color="#1a1a1a",
            corner_radius=15,
            border_width=1,
            border_color="#333"
        )
        frame_np.grid(row=0, column=0, sticky="ew", pady=(10, 25))
        
        ctk.CTkLabel(
            frame_np,
            text=t("gui.header_now_playing"),
            font=("Roboto", 10, "bold"),
            text_color=self.COLOR_SPOTIFY
        ).pack(pady=(15, 5))
        
        self.lbl_np_name = ctk.CTkLabel(
            frame_np,
            text="...",
            font=("Roboto", 22, "bold"),
            text_color="white"
        )
        self.lbl_np_name.pack(pady=0)
        
        self.lbl_np_req = ctk.CTkLabel(
            frame_np,
            text=t("gui.np_waiting"),
            font=("Roboto", 14),
            text_color="gray"
        )
        self.lbl_np_req.pack(pady=(5, 15))
        
        # Queue header
        header_frame = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        header_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text=t("gui.header_queue"),
            font=("Roboto", 20, "bold")
        ).pack(side="left")
        
        self.lbl_queue_stats = ctk.CTkLabel(
            header_frame,
            text="...",
            font=("Roboto", 14),
            text_color="gray"
        )
        self.lbl_queue_stats.pack(side="left", padx=15)
        
        ctk.CTkButton(
            header_frame,
            text=t("gui.btn_clear"),
            width=90,
            height=25,
            fg_color="transparent",
            text_color=self.COLOR_RED,
            hover_color="#333",
            command=self._clear_queue
        ).pack(side="right")
        
        # Queue list
        self.scroll_queue = ctk.CTkScrollableFrame(
            self.frame_main,
            fg_color="transparent"
        )
        self.scroll_queue.grid(row=2, column=0, sticky="nsew")
        
        # Debug log box (row 3, hidden by default)
        self.log_box = ctk.CTkTextbox(
            self.frame_main,
            height=150,
            fg_color="#111",
            text_color="#0f0",
            font=("Consolas", 9)
        )
        # Don't grid it initially - hidden by default
    
    def _setup_control_bar(self):
        """Setup bottom control bar."""
        self.frame_controls = ctk.CTkFrame(
            self,
            height=80,
            fg_color=self.COLOR_PANEL,
            corner_radius=0
        )
        self.frame_controls.grid(row=1, column=1, sticky="ew")
        self.frame_controls.grid_propagate(False)
        
        # Control buttons frame (centered)
        ctrl_frame = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        ctrl_frame.pack(side="right", padx=30, pady=10)
        
        ctk.CTkButton(
            ctrl_frame,
            text=t("gui.btn_force_play"),
            fg_color="#e67e22",
            hover_color="#d35400",
            width=140,
            height=40,
            font=("Roboto", 13, "bold"),
            command=self._force_play
        ).pack(side="left", padx=8)
        
        ctk.CTkButton(
            ctrl_frame,
            text=t("gui.btn_skip"),
            fg_color=self.COLOR_RED,
            hover_color="#c0392b",
            width=120,
            height=40,
            font=("Roboto", 13, "bold"),
            command=self._skip_track
        ).pack(side="left", padx=8)
    
    def _toggle_bot(self):
        """Toggle bot on/off."""
        if self.bot and self.bot.is_running:
            # Stop bot
            self._run_async(self._stop_bot())
        else:
            # Start bot
            if not self.config.twitch.token or not self.config.spotify.client_id:
                self._open_settings()
                return
            
            # Check if Twitch credentials are complete
            if not self.config.twitch.client_id:
                logger.warning("Twitch Client ID missing - using fallback")
            
            self._run_async(self._start_bot())
    
    async def _start_bot(self):
        """Start the bot."""
        try:
            self.bot = BotOrchestrator(self.config, on_update=self._update_ui)
            await self.bot.start()
            
            # Update UI
            self.status_lbl.configure(
                text=t("gui.status_online"),
                text_color=self.COLOR_SPOTIFY
            )
            self.btn_start.configure(
                text=t("gui.btn_stop"),
                fg_color=self.COLOR_RED,
                hover_color="#c0392b"
            )
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            messagebox.showerror("Error", f"Failed to start bot:\n{e}")
    
    async def _stop_bot(self):
        """Stop the bot."""
        if self.bot:
            await self.bot.stop()
            self.bot = None
        
        # Update UI
        self.status_lbl.configure(
            text=t("gui.status_offline"),
            text_color="#7f8c8d"
        )
        self.btn_start.configure(
            text=t("gui.btn_start"),
            fg_color=self.COLOR_SPOTIFY,
            hover_color="#1ed760"
        )
    
    def _on_smart_voting_toggle(self):
        """Handle smart voting toggle."""
        if self.bot:
            enabled = self.smart_voting_var.get()
            self._run_async(self.bot.toggle_smart_voting(enabled))
    
    def _skip_track(self):
        """Skip current track."""
        if self.bot:
            self._run_async(self.bot.skip_current())
    
    def _force_play(self):
        """Force play next track."""
        if self.bot:
            self._run_async(self.bot.force_play_next())
    
    def _clear_queue(self):
        """Clear the queue."""
        if self.bot:
            self._run_async(self.bot.clear_queue())
    
    def _update_ui(self):
        """Update UI with current bot state."""
        self.after(0, self._update_ui_safe)
    
    def _update_ui_safe(self):
        """Update UI (thread-safe)."""
        if not self.bot:
            return
        
        # Update now playing
        current = self.bot.current_track
        if current:
            self.lbl_np_name.configure(text=current.song.full_name)
            self.lbl_np_req.configure(text=f"Requested by: {current.requesters_str}")
        else:
            self.lbl_np_name.configure(text="...")
            self.lbl_np_req.configure(text=t("gui.np_waiting"))
        
        # Update queue
        queue = self.bot.queue_manager.queue
        
        # Clear existing queue items
        for widget in self.scroll_queue.winfo_children():
            widget.destroy()
        
        # Build queue UI
        for i, item in enumerate(queue):
            self._create_queue_card(i, item)
        
        # Update stats
        total_min = math.ceil(self.bot.queue_manager.total_duration_ms / 60000)
        self.lbl_queue_stats.configure(
            text=t("gui.stats_text", count=len(queue), min=total_min)
        )
    
    def _create_queue_card(self, index: int, item):
        """Create a queue item card.
        
        Args:
            index: Position in queue
            item: QueueItem to display
        """
        card = ctk.CTkFrame(
            self.scroll_queue,
            fg_color=self.COLOR_CARD,
            corner_radius=8
        )
        card.pack(fill="x", pady=4, padx=5)
        
        # Info section
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=8)
        
        # Title
        if item.is_manual:
            title_text = f"📌 {item.song.full_name}"
            title_color = "#f1c40f"
            vote_text = ""
        else:
            title_text = f"{index + 1}. {item.song.full_name}"
            title_color = "white"
            vote_text = f" • {item.votes} Votes" if item.votes > 1 and self.smart_voting_var.get() else ""
        
        ctk.CTkLabel(
            info_frame,
            text=title_text,
            font=("Roboto", 14, "bold"),
            text_color=title_color,
            anchor="w"
        ).pack(anchor="w")
        
        # Subtitle
        sub_text = t(
            "gui.card_req_by",
            users=item.requesters_str,
            len=item.song.duration_str,
            votes=vote_text
        )
        
        ctk.CTkLabel(
            info_frame,
            text=sub_text,
            font=("Roboto", 12),
            text_color="#888",
            anchor="w"
        ).pack(anchor="w")
        
        # Buttons section
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        # Unpin button for manual items
        if item.is_manual:
            ctk.CTkButton(
                btn_frame,
                text="⟲",
                width=30,
                height=30,
                fg_color="#444",
                hover_color="#555",
                command=lambda idx=index: self._unpin_item(idx)
            ).pack(side="left", padx=2)
        
        # Move up
        ctk.CTkButton(
            btn_frame,
            text="▲",
            width=30,
            height=30,
            fg_color="#333",
            hover_color="#444",
            command=lambda idx=index: self._move_item(idx, -1)
        ).pack(side="left", padx=2)
        
        # Move down
        ctk.CTkButton(
            btn_frame,
            text="▼",
            width=30,
            height=30,
            fg_color="#333",
            hover_color="#444",
            command=lambda idx=index: self._move_item(idx, 1)
        ).pack(side="left", padx=2)
        
        # Delete
        ctk.CTkButton(
            btn_frame,
            text="✕",
            width=30,
            height=30,
            fg_color=self.COLOR_RED,
            hover_color="#c0392b",
            command=lambda idx=index: self._remove_item(idx)
        ).pack(side="left", padx=(10, 0))
    
    def _move_item(self, index: int, direction: int):
        """Move queue item.
        
        Args:
            index: Item index
            direction: -1 for up, 1 for down
        """
        if self.bot:
            new_index = index + direction
            self._run_async(self.bot.queue_manager.move_item(index, new_index))
            self._update_ui()
    
    def _unpin_item(self, index: int):
        """Unpin queue item.
        
        Args:
            index: Item index
        """
        if self.bot:
            self._run_async(self.bot.queue_manager.unpin_item(index))
            self._update_ui()
    
    def _remove_item(self, index: int):
        """Remove queue item.
        
        Args:
            index: Item index
        """
        if self.bot:
            self._run_async(self.bot.queue_manager.remove_item(index))
            self._update_ui()
    
    def _open_settings(self):
        """Open settings window."""
        from .settings_window import SettingsWindow
        
        if hasattr(self, '_settings_window') and self._settings_window and self._settings_window.winfo_exists():
            self._settings_window.lift()
            return
        
        self._settings_window = SettingsWindow(self, self.config, self._on_settings_saved)
    
    def _on_settings_saved(self, new_config: BotConfig):
        """Handle settings save.
        
        Args:
            new_config: New configuration
        """
        old_lang = self.config.language
        self.config = new_config
        self.config_manager.save(new_config)
        
        if new_config.language != old_lang:
            messagebox.showinfo("Language Changed", t("gui.restart_msg"))
    
    def _open_help(self):
        """Open help window."""
        from .help_window import HelpWindow
        
        if hasattr(self, '_help_window') and self._help_window and self._help_window.winfo_exists():
            self._help_window.lift()
            return
        
        self._help_window = HelpWindow(self)
    
    def _toggle_debug(self):
        """Toggle debug log visibility."""
        self.debug_visible = not self.debug_visible
        
        if self.debug_visible:
            self.log_box.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))
            self.btn_debug.configure(fg_color="#1DB954", text="✔ Debug Log")
        else:
            self.log_box.grid_forget()
            self.btn_debug.configure(fg_color="#222", text="🔍 Debug Log")
    
    def _log_to_gui(self, message: str):
        """Add message to GUI log.
        
        Args:
            message: Log message
        """
        try:
            self.log_box.insert("end", f"> {message}\n")
            self.log_box.see("end")
        except Exception:
            pass
    
    def _run_async(self, coro):
        """Run async coroutine in event loop.
        
        Args:
            coro: Coroutine to run
        """
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            logger.error("Event loop not running")
    
    def _on_close(self):
        """Handle window close."""
        logger.info("Closing application...")
        
        # Disable close button to prevent multiple clicks
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Immediately hide window for better UX
        self.withdraw()
        
        # Run cleanup in background thread
        def cleanup():
            # Stop bot if running
            if self.bot and self.bot.is_running:
                logger.info("Stopping bot...")
                if self.loop and self.loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self.bot.stop(), self.loop)
                    try:
                        future.result(timeout=3)
                        logger.info("Bot stopped successfully")
                    except Exception as e:
                        logger.error(f"Error stopping bot: {e}")
            
            # Save config
            try:
                self.config_manager.save(self.config)
            except Exception as e:
                logger.error(f"Error saving config: {e}")
            
            # Stop event loop
            if self.loop and self.loop.is_running():
                logger.info("Stopping event loop...")
                self.loop.call_soon_threadsafe(self.loop.stop)
                
                # Wait for loop thread
                if self.loop_thread and self.loop_thread.is_alive():
                    self.loop_thread.join(timeout=1)
            
            logger.info("Application closed")
            
            # Force exit (needed because some threads might still be alive)
            import os
            os._exit(0)
        
        # Start cleanup in background
        threading.Thread(target=cleanup, daemon=True).start()
