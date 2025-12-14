"""Statistics window showing song history and stats."""
import customtkinter as ctk
import logging
from tkinter import filedialog, messagebox
from typing import Optional

from ..services.history_manager import HistoryManager

logger = logging.getLogger(__name__)


class StatsWindow(ctk.CTkToplevel):
    """Statistics window for song history and analytics."""
    
    COLOR_BG = "#121212"
    COLOR_PANEL = "#181818"
    COLOR_CARD = "#282828"
    COLOR_SPOTIFY = "#1DB954"
    
    def __init__(self, parent, history_manager: HistoryManager):
        """Initialize stats window.
        
        Args:
            parent: Parent window
            history_manager: History manager instance
        """
        super().__init__(parent)
        
        self.history_manager = history_manager
        
        # Window setup
        self.title("📊 Song Statistics")
        self.geometry("900x700")
        self.configure(fg_color=self.COLOR_BG)
        
        # Time filter
        self.time_filter_var = ctk.StringVar(value="All Time")
        
        self._setup_ui()
        self._refresh_stats()
    
    def _setup_ui(self):
        """Setup UI components."""
        # Header with filter
        header = ctk.CTkFrame(self, fg_color=self.COLOR_PANEL)
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="📊 Statistics",
            font=("Arial", 24, "bold")
        ).pack(side="left", padx=20, pady=15)
        
        # Time filter
        ctk.CTkLabel(header, text="Period:").pack(side="left", padx=(50, 5))
        filter_menu = ctk.CTkOptionMenu(
            header,
            variable=self.time_filter_var,
            values=["All Time", "Last 7 Days", "Last 30 Days"],
            command=lambda _: self._refresh_stats()
        )
        filter_menu.pack(side="left", padx=5)
        
        # Export buttons
        export_frame = ctk.CTkFrame(header, fg_color="transparent")
        export_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(
            export_frame,
            text="📄 Export CSV",
            command=self._export_csv,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            export_frame,
            text="📋 Export JSON",
            command=self._export_json,
            width=120
        ).pack(side="left", padx=5)
        
        # Main content area with tabs
        self.tabview = ctk.CTkTabview(self, fg_color=self.COLOR_PANEL)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create tabs
        self.tabview.add("Overview")
        self.tabview.add("Top Songs")
        self.tabview.add("Top Requesters")
        self.tabview.add("Top Artists")
        
        # Setup each tab
        self._setup_overview_tab()
        self._setup_top_songs_tab()
        self._setup_top_requesters_tab()
        self._setup_top_artists_tab()
    
    def _setup_overview_tab(self):
        """Setup overview tab with summary stats."""
        frame = self.tabview.tab("Overview")
        
        # Stats cards container
        stats_container = ctk.CTkFrame(frame, fg_color="transparent")
        stats_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create stat cards - we'll update these in _refresh_stats
        self.stat_cards = {}
        
        stats_config = [
            ("total_songs", "🎵 Total Songs", "0"),
            ("unique_songs", "🎼 Unique Songs", "0"),
            ("total_requesters", "👥 Total Users", "0"),
            ("skip_rate", "⏭️ Skip Rate", "0%"),
            ("autopilot_percentage", "🤖 Autopilot %", "0%"),
            ("total_duration_hours", "⏱️ Total Hours", "0.0h")
        ]
        
        for i, (key, label, default) in enumerate(stats_config):
            row = i // 2
            col = i % 2
            
            card = ctk.CTkFrame(stats_container, fg_color=self.COLOR_CARD)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            ctk.CTkLabel(
                card,
                text=label,
                font=("Arial", 14)
            ).pack(pady=(20, 5))
            
            value_label = ctk.CTkLabel(
                card,
                text=default,
                font=("Arial", 32, "bold"),
                text_color=self.COLOR_SPOTIFY
            )
            value_label.pack(pady=(5, 20))
            
            self.stat_cards[key] = value_label
        
        # Configure grid
        stats_container.grid_columnconfigure(0, weight=1)
        stats_container.grid_columnconfigure(1, weight=1)
    
    def _setup_top_songs_tab(self):
        """Setup top songs tab."""
        frame = self.tabview.tab("Top Songs")
        
        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(frame, fg_color=self.COLOR_PANEL)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.top_songs_frame = scroll
    
    def _setup_top_requesters_tab(self):
        """Setup top requesters tab."""
        frame = self.tabview.tab("Top Requesters")
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color=self.COLOR_PANEL)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.top_requesters_frame = scroll
    
    def _setup_top_artists_tab(self):
        """Setup top artists tab."""
        frame = self.tabview.tab("Top Artists")
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color=self.COLOR_PANEL)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.top_artists_frame = scroll
    
    def _refresh_stats(self):
        """Refresh all statistics."""
        # Get days filter
        days_map = {"All Time": 0, "Last 7 Days": 7, "Last 30 Days": 30}
        days = days_map[self.time_filter_var.get()]
        
        # Update overview
        stats = self.history_manager.get_stats_summary(days)
        self.stat_cards["total_songs"].configure(text=str(stats["total_songs"]))
        self.stat_cards["unique_songs"].configure(text=str(stats["unique_songs"]))
        self.stat_cards["total_requesters"].configure(text=str(stats["total_requesters"]))
        self.stat_cards["skip_rate"].configure(text=f"{stats['skip_rate']:.1f}%")
        self.stat_cards["autopilot_percentage"].configure(text=f"{stats['autopilot_percentage']:.1f}%")
        self.stat_cards["total_duration_hours"].configure(text=f"{stats['total_duration_hours']:.1f}h")
        
        # Update top songs
        self._update_top_songs(days)
        self._update_top_requesters(days)
        self._update_top_artists(days)
    
    def _update_top_songs(self, days: int):
        """Update top songs list."""
        # Clear existing
        for widget in self.top_songs_frame.winfo_children():
            widget.destroy()
        
        top_songs = self.history_manager.get_top_songs(limit=10, days=days)
        
        if not top_songs:
            ctk.CTkLabel(
                self.top_songs_frame,
                text="No songs played yet",
                font=("Arial", 14)
            ).pack(pady=20)
            return
        
        for i, (song, artist, count) in enumerate(top_songs, 1):
            card = ctk.CTkFrame(self.top_songs_frame, fg_color=self.COLOR_CARD)
            card.pack(fill="x", pady=5)
            
            # Rank
            ctk.CTkLabel(
                card,
                text=f"#{i}",
                font=("Arial", 18, "bold"),
                width=40
            ).pack(side="left", padx=(20, 10), pady=15)
            
            # Song info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            ctk.CTkLabel(
                info_frame,
                text=song,
                font=("Arial", 14, "bold"),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame,
                text=artist,
                font=("Arial", 12),
                text_color="gray",
                anchor="w"
            ).pack(anchor="w")
            
            # Play count
            ctk.CTkLabel(
                card,
                text=f"{count}x",
                font=("Arial", 16, "bold"),
                text_color=self.COLOR_SPOTIFY
            ).pack(side="right", padx=20)
    
    def _update_top_requesters(self, days: int):
        """Update top requesters list."""
        for widget in self.top_requesters_frame.winfo_children():
            widget.destroy()
        
        top_requesters = self.history_manager.get_top_requesters(limit=10, days=days)
        
        if not top_requesters:
            ctk.CTkLabel(
                self.top_requesters_frame,
                text="No requests yet",
                font=("Arial", 14)
            ).pack(pady=20)
            return
        
        for i, (username, count) in enumerate(top_requesters, 1):
            card = ctk.CTkFrame(self.top_requesters_frame, fg_color=self.COLOR_CARD)
            card.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                card,
                text=f"#{i}",
                font=("Arial", 18, "bold"),
                width=40
            ).pack(side="left", padx=(20, 10), pady=15)
            
            ctk.CTkLabel(
                card,
                text=username,
                font=("Arial", 14, "bold"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10)
            
            ctk.CTkLabel(
                card,
                text=f"{count} songs",
                font=("Arial", 14),
                text_color=self.COLOR_SPOTIFY
            ).pack(side="right", padx=20)
    
    def _update_top_artists(self, days: int):
        """Update top artists list."""
        for widget in self.top_artists_frame.winfo_children():
            widget.destroy()
        
        top_artists = self.history_manager.get_top_artists(limit=10, days=days)
        
        if not top_artists:
            ctk.CTkLabel(
                self.top_artists_frame,
                text="No artists yet",
                font=("Arial", 14)
            ).pack(pady=20)
            return
        
        for i, (artist, count) in enumerate(top_artists, 1):
            card = ctk.CTkFrame(self.top_artists_frame, fg_color=self.COLOR_CARD)
            card.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                card,
                text=f"#{i}",
                font=("Arial", 18, "bold"),
                width=40
            ).pack(side="left", padx=(20, 10), pady=15)
            
            ctk.CTkLabel(
                card,
                text=artist,
                font=("Arial", 14, "bold"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=10)
            
            ctk.CTkLabel(
                card,
                text=f"{count}x",
                font=("Arial", 16, "bold"),
                text_color=self.COLOR_SPOTIFY
            ).pack(side="right", padx=20)
    
    def _export_csv(self):
        """Export history to CSV."""
        filepath = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if filepath:
            try:
                self.history_manager.export_to_csv(filepath)
                messagebox.showinfo("Success", f"Exported to {filepath}")
            except Exception as e:
                logger.error(f"Export failed: {e}")
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def _export_json(self):
        """Export history to JSON."""
        filepath = filedialog.asksaveasfilename(
            title="Export to JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if filepath:
            try:
                self.history_manager.export_to_json(filepath)
                messagebox.showinfo("Success", f"Exported to {filepath}")
            except Exception as e:
                logger.error(f"Export failed: {e}")
                messagebox.showerror("Error", f"Export failed: {e}")
