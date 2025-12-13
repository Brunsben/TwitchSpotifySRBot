"""Help and documentation window."""
import webbrowser

import customtkinter as ctk

from ..utils.i18n import t


class HelpWindow(ctk.CTkToplevel):
    """Help and documentation window."""
    
    def __init__(self, parent):
        """Initialize help window.
        
        Args:
            parent: Parent window
        """
        super().__init__(parent)
        
        self.title(t("help.title"))
        self.geometry("700x800")
        self.attributes("-topmost", True)
        
        # Link buttons
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            link_frame,
            text=t("help.btn_token"),
            fg_color="#9146FF",
            hover_color="#772ce8",
            command=lambda: webbrowser.open("https://dev.twitch.tv/console/apps")
        ).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(
            link_frame,
            text=t("help.btn_dev"),
            fg_color="#1DB954",
            hover_color="#1aa34a",
            command=lambda: webbrowser.open("https://developer.spotify.com/dashboard/")
        ).pack(side="left", expand=True, padx=5)
        
        # Help text
        text_box = ctk.CTkTextbox(
            self,
            font=("Consolas", 12),
            fg_color="#222",
            text_color="#eee",
            wrap="word"
        )
        text_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        text_box.insert("0.0", t("help.text"))
        text_box.configure(state="disabled")
