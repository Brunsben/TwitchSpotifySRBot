import customtkinter as ctk
import threading
from twitchio.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import asyncio
import os
import json
import time
import sys
import math
import random
import webbrowser
from tkinter import messagebox

# --- KONFIGURATION ---
CONFIG_FILE = "config_premium.json"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Mapping: Anzeigename -> Dateiname
LANG_FILES = {
    "Deutsch": "lang_de.json",
    "English": "lang_en.json" 
}

# --- STANDARD SPRACH-DATEI (Deutsch) ---
DEFAULT_LANG_DE = {
    "gui": {
        "title": "Twitch SR Bot - V34",
        "status_online": "ONLINE",
        "status_offline": "OFFLINE",
        "btn_start": "STARTEN",
        "btn_stop": "STOPPEN",
        "btn_settings": "Einstellungen ⚙️",
        "btn_help": "Hilfe & Anleitung 📖",
        "switch_smart": "Smart Voting",
        "header_now_playing": "A K T U E L L",
        "np_waiting": "Warten auf Start...",
        "header_queue": "Warteschlange",
        "btn_clear": "Alle löschen 🗑",
        "btn_force_play": "▶ Force Play",
        "btn_skip": "⏭ Skip",
        "stats_text": "({count} Tracks • ca. {min} Min)",
        "card_req_by": "Von: {users} | {len}{votes}",
        "restart_msg": "Bitte starte das Programm neu, um die Sprache zu ändern.",
        "credits": "Dev: uprisin6 | V34.0"
    },
    "settings": {
        "title": "Einstellungen",
        "lbl_lang": "Sprache / Language",
        "group_twitch": "Twitch Einrichtung",
        "lbl_channel": "Dein Kanalname (Wo soll der Bot hin?)",
        "desc_channel": "Der Name deines Twitch-Kanals (z.B. 'uprisin6').",
        "lbl_token": "Twitch Chat Token (Wer schreibt?)",
        "desc_token": "Token des Accounts, der im Chat antwortet.",
        "group_spotify": "Spotify API Einrichtung",
        "lbl_sp_id": "Spotify Client ID",
        "lbl_sp_secret": "Spotify Client Secret",
        "lbl_fallback": "Autopilot Playlist (Backup Musik)",
        "desc_fallback": "Link zu einer ÖFFENTLICHEN Playlist kopieren.",
        "group_rules": "Regeln & Limits",
        "lbl_max_q": "Max. Songs in Warteschlange",
        "lbl_max_user": "Max. Wünsche pro User",
        "lbl_max_len": "Max. Länge (Minuten)",
        "lbl_cooldown": "Cooldown pro Song (Minuten)",
        "btn_save": "SPEICHERN & PRÜFEN",
        "msg_saved": "Einstellungen gespeichert.",
        "err_playlist_title": "Playlist Problem",
        "err_playlist_body": "Die Autopilot-Playlist konnte nicht geladen werden.\nFehler: 404 Not Found.\n\nBitte stelle sicher, dass die Playlist 'Öffentlich' ist."
    },
    "chat": {
        "ready": "Twitch Chat: {botname} ist bereit!",
        "queue_full": "@{user} Die Warteschlange ist leider voll ({max} Songs).",
        "limit_reached": "@{user} Du hast dein Song-Limit erreicht ({max} Songs parallel).",
        "added_pos": "@{user} -> {song} hinzugefügt (Platz {pos}, ca. {wait} Min).",
        "added_simple": "@{user} -> {song} zur Warteschlange hinzugefügt.",
        "err_too_long": "@{user} Dieser Song ist zu lang (Max: {max} Min).",
        "err_cooldown": "@{user} Dieser Song wurde vor Kurzem erst gespielt.",
        "err_not_found": "@{user} Konnte den Song nicht finden. Prüfe Schreibweise oder Link."
    },
    "logs": {
        "vote": "[VOTE] {name} (+1)",
        "new_song": "[NEU] {name} ({user})",
        "play": "[PLAY] {name}",
        "queue": "[QUEUE] An Spotify gesendet: {name}",
        "auto_start": "[AUTO] Fallback Track: {name}",
        "auto_error": "[ERR] Autopilot Fehler ({count}/3): {err}",
        "auto_stop": "[STOP] Autopilot deaktiviert (Playlist prüfen)."
    },
    "help": {
        "title": "Hilfe & Dokumentation",
        "btn_token": "Twitch Token Generator 🔗",
        "btn_dev": "Spotify Dashboard 🔗",
        "text": """★ HILFE - V34 ★

Dies ist die offizielle Dokumentation für den Twitch Spotify Bot (Dev: uprisin6).

1. ERSTE SCHRITTE
- Klicke auf 'Einstellungen'.
- Trage deinen Twitch Kanalnamen ein (kleingeschrieben).
- Hole dir einen OAuth Token (Button oben 'Twitch Token Generator') und füge ihn bei 'Token' ein.
- Erstelle eine App im Spotify Dashboard, trage Client ID & Secret ein.

2. AUTOPILOT (FALLBACK)
- Erstelle eine Playlist auf Spotify.
- Setze sie auf 'Öffentlich' (Wichtig!).
- Kopiere den Link und füge ihn in den Einstellungen ein.
- Wenn keine Wünsche mehr da sind, spielt der Bot daraus Songs.

3. ABSTÜRZE VERMEIDEN (Mac/Linux)
- Diese Version nutzt 'Thread-Safe Mode'.
- Sollte der Bot dennoch abstürzen, starte ihn neu.

4. COMMANDS IM CHAT
- !sr [Songname] -> Sucht und fügt Song hinzu.
- !sr [Spotify Link] -> Fügt direkten Link hinzu.

Viel Spaß beim Streamen!
"""
    }
}

class BotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config laden (für Sprache)
        self.config_data = {
            "language": "Deutsch",
            "channel": "", "token": "", "sp_id": "", "sp_secret": "", 
            "fallback_id": "", "max_queue": "20", "max_user_reqs": "3",
            "max_song_len_min": "10", "song_cooldown_min": "30"
        }
        self.load_config_file()

        # Sprache laden
        self.texts = DEFAULT_LANG_DE
        self.load_language_file()

        # Theme Setup
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green") 

        self.title(self.t("gui.title"))
        self.geometry("1200x900")
        self.configure(fg_color="#121212")
        self.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # Logic Vars
        self.is_active = False        
        self.queue_data = [] 
        self.current_track_obj = None 
        self.history_data = {} 
        self.sp_client = None 
        self.device_id = None 
        self.twitch_bot = None
        self.autopilot_error_count = 0
        
        # Colors
        self.COLOR_BG = "#121212"
        self.COLOR_PANEL = "#181818"
        self.COLOR_CARD = "#282828"
        self.COLOR_SPOTIFY = "#1DB954"
        self.COLOR_RED = "#e74c3c"

        # Layout
        self.grid_columnconfigure(0, weight=0, minsize=320) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_area()
        self.create_control_bar()

    # --- LANGUAGE SYSTEM ---
    def load_language_file(self):
        selected_lang = self.config_data.get("language", "Deutsch")
        filename = LANG_FILES.get(selected_lang, "lang_de.json")

        if not os.path.exists(filename):
            if selected_lang == "Deutsch":
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(DEFAULT_LANG_DE, f, indent=4, ensure_ascii=False)
                except: pass
        else:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    self.texts = json.load(f)
            except: 
                print(f"Fehler beim Laden von {filename}. Nutze Fallback.")

    def t(self, key_path):
        try:
            keys = key_path.split(".")
            val = self.texts
            for k in keys:
                val = val[k]
            return val
        except:
            return f"[{key_path}]"

    # --- GUI CREATION ---
    def create_sidebar(self):
        self.frame_side = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=self.COLOR_PANEL)
        self.frame_side.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(self.frame_side, text="DJ BOT", font=("Roboto", 28, "bold"), text_color="white").pack(pady=(40, 5))
        self.status_lbl = ctk.CTkLabel(self.frame_side, text=self.t("gui.status_offline"), text_color="#7f8c8d", font=("Roboto", 14, "bold"))
        self.status_lbl.pack(pady=(0, 20))

        self.check_smart_var = ctk.BooleanVar(value=True)
        sw = ctk.CTkSwitch(self.frame_side, text=self.t("gui.switch_smart"), variable=self.check_smart_var, command=self.update_mode_label,
                           font=("Roboto", 14), progress_color=self.COLOR_SPOTIFY)
        sw.pack(pady=20, padx=40, anchor="w")

        ctk.CTkButton(self.frame_side, text=self.t("gui.btn_settings"), fg_color="#333", hover_color="#444", 
                      font=("Roboto", 14), height=40, command=self.open_settings_window).pack(fill="x", padx=30, pady=10)

        ctk.CTkButton(self.frame_side, text=self.t("gui.btn_help"), fg_color="#333", hover_color="#444", 
                      font=("Roboto", 14), height=40, command=self.open_help_window).pack(fill="x", padx=30, pady=10)

        # Spacer
        ctk.CTkLabel(self.frame_side, text="").pack(expand=True)

        self.btn_start = ctk.CTkButton(self.frame_side, text=self.t("gui.btn_start"), fg_color=self.COLOR_SPOTIFY, hover_color="#1ed760",
                                       height=60, font=("Roboto", 18, "bold"), corner_radius=30, command=self.toggle_bot)
        self.btn_start.pack(fill="x", padx=30, pady=(40, 20))
        
        # CREDITS (Unten angefügt)
        ctk.CTkLabel(self.frame_side, text=self.t("gui.credits"), text_color="#555", font=("Arial", 10)).pack(side="bottom", pady=10)

    def create_main_area(self):
        self.frame_main = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.frame_main.grid_rowconfigure(2, weight=1)
        self.frame_main.grid_columnconfigure(0, weight=1)

        # Now Playing
        self.frame_np = ctk.CTkFrame(self.frame_main, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333")
        self.frame_np.grid(row=0, column=0, sticky="ew", pady=(10, 25))

        lbl_title = ctk.CTkLabel(self.frame_np, text=self.t("gui.header_now_playing"), font=("Roboto", 10, "bold"), text_color=self.COLOR_SPOTIFY)
        lbl_title.pack(pady=(15, 5))

        self.lbl_np_name = ctk.CTkLabel(self.frame_np, text="...", font=("Roboto", 22, "bold"), text_color="white")
        self.lbl_np_name.pack(pady=0)

        self.lbl_np_req = ctk.CTkLabel(self.frame_np, text=self.t("gui.np_waiting"), font=("Roboto", 14), text_color="gray")
        self.lbl_np_req.pack(pady=(5, 15))

        # Queue Header
        header_frame = ctk.CTkFrame(self.frame_main, fg_color="transparent")
        header_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(header_frame, text=self.t("gui.header_queue"), font=("Roboto", 20, "bold")).pack(side="left")
        self.lbl_queue_stats = ctk.CTkLabel(header_frame, text="...", font=("Roboto", 14), text_color="gray")
        self.lbl_queue_stats.pack(side="left", padx=15)

        ctk.CTkButton(header_frame, text=self.t("gui.btn_clear"), width=90, height=25, fg_color="transparent", 
                      text_color="#e74c3c", hover_color="#333", command=self.admin_clear).pack(side="right")

        # List
        self.scroll_queue = ctk.CTkScrollableFrame(self.frame_main, fg_color="transparent")
        self.scroll_queue.grid(row=2, column=0, sticky="nsew")

    def create_control_bar(self):
        self.frame_controls = ctk.CTkFrame(self, height=70, fg_color=self.COLOR_PANEL, corner_radius=0)
        self.frame_controls.grid(row=1, column=1, sticky="ew")
        
        self.log_box = ctk.CTkTextbox(self.frame_controls, height=50, width=400, fg_color="#111", text_color="#888", font=("Consolas", 10))
        self.log_box.pack(side="left", padx=20, pady=10)
        
        ctrl_frame = ctk.CTkFrame(self.frame_controls, fg_color="transparent")
        ctrl_frame.pack(side="right", padx=20)

        ctk.CTkButton(ctrl_frame, text=self.t("gui.btn_force_play"), fg_color="#e67e22", hover_color="#d35400", width=120, command=self.force_play_next).pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text=self.t("gui.btn_skip"), fg_color=self.COLOR_RED, hover_color="#c0392b", width=100, command=self.admin_skip).pack(side="left", padx=5)

    # --- SETTINGS & HELP ---
    def open_help_window(self):
        if hasattr(self, 'win_help') and self.win_help is not None and self.win_help.winfo_exists():
            self.win_help.lift()
            return
        
        self.win_help = ctk.CTkToplevel(self)
        self.win_help.geometry("700x800")
        self.win_help.title(self.t("help.title"))
        self.win_help.attributes("-topmost", True)

        link_frame = ctk.CTkFrame(self.win_help, fg_color="transparent")
        link_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(link_frame, text=self.t("help.btn_token"), fg_color="#9146FF", hover_color="#772ce8",
                      command=lambda: webbrowser.open("https://twitchapps.com/tmi/")).pack(side="left", expand=True, padx=5)
        
        ctk.CTkButton(link_frame, text=self.t("help.btn_dev"), fg_color="#1DB954", hover_color="#1aa34a",
                      command=lambda: webbrowser.open("https://developer.spotify.com/dashboard/")).pack(side="left", expand=True, padx=5)

        txt = ctk.CTkTextbox(self.win_help, font=("Consolas", 12), fg_color="#222", text_color="#eee", wrap="word")
        txt.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        txt.insert("0.0", self.t("help.text"))
        txt.configure(state="disabled")

    def open_settings_window(self):
        if hasattr(self, 'toplevel_settings') and self.toplevel_settings is not None and self.toplevel_settings.winfo_exists():
            self.toplevel_settings.lift()
            return
        
        # Kleines Fenster, damit es überall passt
        self.toplevel_settings = ctk.CTkToplevel(self)
        self.toplevel_settings.geometry("500x600") 
        self.toplevel_settings.title(self.t("settings.title"))
        self.toplevel_settings.attributes("-topmost", True)
        
        # Grid Setup für das Settings Fenster:
        # Row 0: Scrollbereich (flexibel)
        # Row 1: Footer mit Button (fest)
        self.toplevel_settings.grid_rowconfigure(0, weight=1)
        self.toplevel_settings.grid_columnconfigure(0, weight=1)

        # 1. SCROLL BEREICH
        scroll_frame = ctk.CTkScrollableFrame(self.toplevel_settings, fg_color="#222")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))

        ctk.CTkLabel(scroll_frame, text=self.t("settings.lbl_lang"), anchor="w", text_color="#ccc").pack(fill="x", padx=20, pady=(20,5))
        self.combo_lang = ctk.CTkComboBox(scroll_frame, values=["Deutsch"], state="readonly") 
        self.combo_lang.set(self.config_data.get("language", "Deutsch"))
        self.combo_lang.pack(fill="x", padx=20)

        ctk.CTkLabel(scroll_frame, text=self.t("settings.group_twitch"), font=("Roboto", 18, "bold")).pack(pady=(30, 10))
        self.entry_channel = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_channel"), self.config_data['channel'])
        ctk.CTkLabel(scroll_frame, text=self.t("settings.desc_channel"), font=("Arial", 11), text_color="gray").pack(pady=(0, 10))
        
        self.entry_token = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_token"), self.config_data['token'], show="*")
        ctk.CTkLabel(scroll_frame, text=self.t("settings.desc_token"), font=("Arial", 11), text_color="#e67e22").pack(pady=(0, 10))
        
        ctk.CTkFrame(scroll_frame, height=2, fg_color="#444").pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(scroll_frame, text=self.t("settings.group_spotify"), font=("Roboto", 18, "bold")).pack(pady=10)
        self.entry_sp_id = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_sp_id"), self.config_data['sp_id'])
        self.entry_sp_secret = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_sp_secret"), self.config_data['sp_secret'], show="*")
        
        ctk.CTkFrame(scroll_frame, height=2, fg_color="#444").pack(fill="x", padx=20, pady=10)
        self.entry_fallback_id = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_fallback"), self.config_data.get('fallback_id', ''))
        ctk.CTkLabel(scroll_frame, text=self.t("settings.desc_fallback"), font=("Arial", 11), text_color="gray").pack(pady=(0, 10))

        ctk.CTkFrame(scroll_frame, height=2, fg_color="#444").pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(scroll_frame, text=self.t("settings.group_rules"), font=("Roboto", 18, "bold")).pack(pady=10)

        self.entry_max_queue = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_max_q"), self.config_data['max_queue'])
        self.entry_max_user_reqs = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_max_user"), self.config_data.get('max_user_reqs', '3'))
        self.entry_max_len = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_max_len"), self.config_data.get('max_song_len_min', '10'))
        self.entry_cooldown = self.add_input_to_scroll(scroll_frame, self.t("settings.lbl_cooldown"), self.config_data.get('song_cooldown_min', '30'))

        # Zusatzabstand im Scrollframe unten, damit nichts verdeckt wird vom Rand
        ctk.CTkLabel(scroll_frame, text="").pack(pady=10)

        # 2. FOOTER (Fester Bereich)
        pnl_footer = ctk.CTkFrame(self.toplevel_settings, height=80, fg_color="#111")
        pnl_footer.grid(row=1, column=0, sticky="ew")
        
        ctk.CTkButton(pnl_footer, text=self.t("settings.btn_save"), fg_color=self.COLOR_SPOTIFY, height=45, 
                      font=("Roboto", 14, "bold"), command=self.save_settings_from_top).pack(padx=40, pady=15, fill="x")

    def add_input_to_scroll(self, parent, label, val, show=None):
        ctk.CTkLabel(parent, text=label, anchor="w", text_color="#ccc").pack(fill="x", padx=20, pady=(5,0))
        entry = ctk.CTkEntry(parent, show=show, fg_color="#333", border_color="#555")
        entry.insert(0, str(val))
        entry.pack(fill="x", padx=20, pady=(2,5))
        return entry

    def clean_playlist_id(self, raw_id):
        if not raw_id: return ""
        if "playlist/" in raw_id:
            try: return raw_id.split("playlist/")[1].split("?")[0]
            except: pass
        if "spotify:playlist:" in raw_id: return raw_id.split(":")[-1]
        return raw_id.strip()

    def save_settings_from_top(self):
        new_lang = self.combo_lang.get()
        needs_restart = new_lang != self.config_data.get("language")
        
        self.config_data['language'] = new_lang
        self.config_data['channel'] = self.entry_channel.get().strip()
        self.config_data['token'] = self.entry_token.get().strip()
        self.config_data['sp_id'] = self.entry_sp_id.get().strip()
        self.config_data['sp_secret'] = self.entry_sp_secret.get().strip()
        
        raw_pl = self.entry_fallback_id.get().strip()
        clean_pl = self.clean_playlist_id(raw_pl)
        self.config_data['fallback_id'] = clean_pl
        
        self.config_data['max_queue'] = self.entry_max_queue.get().strip()
        self.config_data['max_user_reqs'] = self.entry_max_user_reqs.get().strip()
        self.config_data['max_song_len_min'] = self.entry_max_len.get().strip()
        self.config_data['song_cooldown_min'] = self.entry_cooldown.get().strip()
        
        if clean_pl and self.sp_client:
            try:
                self.sp_client.playlist(clean_pl)
                self.log(f"Playlist ID '{clean_pl}' Check: OK.")
            except Exception as e:
                ctk.CTkMessagebox(title=self.t("settings.err_playlist_title"), message=self.t("settings.err_playlist_body"), icon="warning")
                self.log("Playlist Check FEHLGESCHLAGEN.")
        
        self.save_config_file()
        self.toplevel_settings.destroy()
        
        self.log(self.t("settings.msg_saved"))
        if needs_restart:
            messagebox.showinfo("Sprache geändert", self.t("gui.restart_msg"))

    # --- CORE ---
    def load_config_file(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for k, v in data.items(): self.config_data[k] = v
            except: pass

    def save_config_file(self):
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(self.config_data, f)
        except: pass

    def on_close_window(self):
        self.save_config_file()
        self.is_active = False
        self.destroy()
        sys.exit()

    # --- THREAD SAFE LOGGING ---
    def log(self, text):
        print(text)
        self.after(0, lambda: self._log_gui(text))

    def _log_gui(self, text):
        try:
            self.log_box.insert("end", f"> {text}\n")
            self.log_box.see("end")
        except: pass

    # --- SONG & QUEUE LOGIC ---
    def move_song(self, index, direction):
        if not self.queue_data: return
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.queue_data): return
        self.queue_data[index], self.queue_data[new_index] = self.queue_data[new_index], self.queue_data[index]
        self.queue_data[index]['is_manual'] = True
        self.queue_data[new_index]['is_manual'] = True
        self.sort_and_update_ui()

    def unpin_song(self, song_obj):
        song_obj['is_manual'] = False
        self.sort_and_update_ui()

    def sort_and_update_ui(self):
        # NP
        if self.current_track_obj:
             self.lbl_np_name.configure(text=self.current_track_obj['name'])
             reqs = ", ".join(self.current_track_obj['reqs'])
             self.lbl_np_req.configure(text=f"Requested by: {reqs}")
        else:
             self.lbl_np_name.configure(text="...")
             self.lbl_np_req.configure(text=self.t("gui.np_waiting"))

        # Sort
        manuals = [s for s in self.queue_data if s.get('is_manual')]
        autos = [s for s in self.queue_data if not s.get('is_manual')]
        if self.check_smart_var.get():
            autos.sort(key=lambda x: x['votes'], reverse=True)
        self.queue_data = manuals + autos
        
        # Build UI
        for widget in self.scroll_queue.winfo_children(): widget.destroy()

        total_ms = 0
        for i, s in enumerate(self.queue_data):
            total_ms += s['duration']
            
            card = ctk.CTkFrame(self.scroll_queue, fg_color=self.COLOR_CARD, corner_radius=8)
            card.pack(fill="x", pady=4, padx=5)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=8)
            
            req_names = ", ".join(s['reqs'])
            
            if s.get('is_manual'):
                title_text = f"📌 {s['name']}"
                v_text = ""
                title_color = "#f1c40f"
            else:
                title_text = f"{i+1}. {s['name']}"
                v_text = f" • {s['votes']} Votes" if s['votes'] > 1 and self.check_smart_var.get() else ""
                title_color = "white"
            
            sub_text = self.t("gui.card_req_by").format(users=req_names, len=s['len_str'], votes=v_text)

            ctk.CTkLabel(info_frame, text=title_text, font=("Roboto", 14, "bold"), text_color=title_color, anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=sub_text, font=("Roboto", 12), text_color="#888", anchor="w").pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)

            if s.get('is_manual'):
                ctk.CTkButton(btn_frame, text="⟲", width=30, height=30, fg_color="#444", hover_color="#555",
                              command=lambda obj=s: self.unpin_song(obj)).pack(side="left", padx=2)

            ctk.CTkButton(btn_frame, text="▲", width=30, height=30, fg_color="#333", hover_color="#444",
                          command=lambda idx=i: self.move_song(idx, -1)).pack(side="left", padx=2)
            
            ctk.CTkButton(btn_frame, text="▼", width=30, height=30, fg_color="#333", hover_color="#444",
                          command=lambda idx=i: self.move_song(idx, 1)).pack(side="left", padx=2)

            ctk.CTkButton(btn_frame, text="✕", width=30, height=30, fg_color=self.COLOR_RED, hover_color="#c0392b",
                          command=lambda obj=s: self.delete_specific_song(obj)).pack(side="left", padx=(10, 0))

        total_min = math.ceil(total_ms / 60000)
        self.lbl_queue_stats.configure(text=self.t("gui.stats_text").format(count=len(self.queue_data), min=total_min))

    def delete_specific_song(self, song_obj):
        if song_obj in self.queue_data:
            self.queue_data.remove(song_obj)
            self.sort_and_update_ui()

    def admin_skip(self):
        try: self.sp_client.next_track(device_id=self.device_id)
        except: pass

    def force_play_next(self):
        self.play_next_song(force_start=True)

    def admin_clear(self):
        self.queue_data = []
        self.update_ui_safe()

    def update_mode_label(self):
        self.update_ui_safe()

    # --- PROCESS LOGIC ---
    def toggle_bot(self):
        if not self.is_active:
            if not self.config_data['token'] or not self.config_data['sp_id']:
                self.open_settings_window()
                return
            self.is_active = True
            self.status_lbl.configure(text=self.t("gui.status_online"), text_color=self.COLOR_SPOTIFY)
            self.btn_start.configure(text=self.t("gui.btn_stop"), fg_color=self.COLOR_RED, hover_color="#c0392b")
            threading.Thread(target=self.run_process, daemon=True).start()
        else:
            self.is_active = False
            self.status_lbl.configure(text=self.t("gui.status_offline"), text_color="#7f8c8d")
            self.btn_start.configure(text=self.t("gui.btn_start"), fg_color=self.COLOR_SPOTIFY, hover_color="#1ed760")
            self.log("Bot halted.")

    def run_process(self):
        try:
            conf = self.config_data
            scope = "user-modify-playback-state user-read-currently-playing user-read-playback-state playlist-read-private playlist-read-collaborative"
            
            auth = SpotifyOAuth(client_id=conf['sp_id'], client_secret=conf['sp_secret'], redirect_uri=REDIRECT_URI, scope=scope)
            self.sp_client = spotipy.Spotify(auth_manager=auth)
            self.refresh_device()
            self.log("Spotify connected.")
        except Exception as e:
            self.log(f"Login Error: {e}")
            self.is_active = False
            return
        threading.Thread(target=self.logic_loop, daemon=True).start()
        self.run_twitch_bot(conf['token'], conf['channel'])

    def refresh_device(self):
        try:
            devices = self.sp_client.devices()
            if devices and devices['devices']:
                for d in devices['devices']:
                    if d['is_active']:
                        self.device_id = d['id']
                        return
                self.device_id = devices['devices'][0]['id']
        except: pass

    def logic_loop(self):
        while self.is_active:
            time.sleep(4)
            try:
                curr = self.sp_client.current_playback()
                is_playing = curr and curr['is_playing']
                
                if not self.queue_data:
                    if not is_playing:
                        self.play_fallback_track()
                    else:
                        if curr['item']:
                            rem = curr['item']['duration_ms'] - curr['progress_ms']
                            if rem < 6000: pass 
                    continue

                if not is_playing:
                    self.play_next_song(force_start=True)
                    continue
                
                if curr['item']:
                    rem = curr['item']['duration_ms'] - curr['progress_ms']
                    if rem < 10000:
                        self.play_next_song(force_start=False)
                        time.sleep(8) 
            except Exception as e: pass

    def play_fallback_track(self):
        f_id = self.config_data.get('fallback_id', '').strip()
        if not f_id: return
        
        if self.autopilot_error_count > 3: return 

        try:
            if not self.device_id: self.refresh_device()
            
            pl = self.sp_client.playlist_tracks(f_id, fields="total", limit=1)
            total = pl['total']
            if total == 0: return

            offset = random.randint(0, total-1)
            results = self.sp_client.playlist_items(f_id, limit=1, offset=offset)
            track = results['items'][0]['track']
            
            self.sp_client.start_playback(device_id=self.device_id, uris=[track['uri']])
            
            self.current_track_obj = {
                'name': f"{track['name']} - {track['artists'][0]['name']}",
                'reqs': ["🤖 Autopilot"]
            }
            self.log(self.t("logs.auto_start").format(name=track['name']))
            self.update_ui_safe()
            self.autopilot_error_count = 0 
            time.sleep(5)
        except Exception as e:
            self.autopilot_error_count += 1
            self.log(self.t("logs.auto_error").format(count=self.autopilot_error_count, err=e))
            if self.autopilot_error_count > 3:
                self.log(self.t("logs.auto_stop"))
            time.sleep(10)

    def play_next_song(self, force_start=False):
        if not self.queue_data: return
        next_obj = self.queue_data.pop(0)
        self.current_track_obj = next_obj
        
        self.update_ui_safe()
        
        try:
            if not self.device_id: self.refresh_device()
            if force_start:
                self.sp_client.start_playback(device_id=self.device_id, uris=[next_obj['uri']])
                self.log(self.t("logs.play").format(name=next_obj['name']))
            else:
                self.sp_client.add_to_queue(next_obj['uri'], device_id=self.device_id)
                self.log(self.t("logs.queue").format(name=next_obj['name']))
        except Exception as e:
            self.log(f"Playback Error: {e}")

    # --- TWITCH ---
    def run_twitch_bot(self, token, channel):
        self.bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.bot_loop)
        if not token.startswith("oauth:"): token = f"oauth:{token}"
        gui = self
        class Bot(commands.Bot):
            def __init__(self):
                super().__init__(token=token, prefix='!', initial_channels=[channel])
            async def event_ready(self):
                gui.log(gui.t("chat.ready").format(botname=self.nick))
            async def event_message(self, message):
                if not gui.is_active or message.echo: return
                await self.handle_commands(message)
            @commands.command(name='sr')
            async def command_sr(self, ctx):
                if not gui.is_active: return
                user = ctx.author.name
                
                try: max_q = int(gui.config_data['max_queue'])
                except: max_q = 20
                if len(gui.queue_data) >= max_q:
                    await ctx.send(gui.t("chat.queue_full").format(user=user, max=max_q))
                    return
                
                try: max_u = int(gui.config_data.get('max_user_reqs', 3))
                except: max_u = 3
                current_user_reqs = 0
                for s in gui.queue_data:
                    if user in s['reqs']: current_user_reqs += 1
                if current_user_reqs >= max_u:
                    await ctx.send(gui.t("chat.limit_reached").format(user=user, max=max_u))
                    return

                query = ctx.message.content.replace('!sr', '').strip()
                if len(query) > 1:
                    result = gui.handle_request_sync(query, user)
                    if isinstance(result, dict):
                        try:
                            idx = gui.queue_data.index(result)
                            pos = idx + 1
                            wait_ms = sum(s['duration'] for s in gui.queue_data[:idx])
                            wait_min = int(wait_ms / 60000)
                            msg = gui.t("chat.added_pos").format(user=user, song=result['name'], pos=pos, wait=wait_min)
                        except:
                            msg = gui.t("chat.added_simple").format(user=user, song=result['name'])
                        await ctx.send(msg)
                    elif result == "ERR_TOO_LONG":
                        try: mm = int(gui.config_data.get('max_song_len_min', 10))
                        except: mm = 10
                        await ctx.send(gui.t("chat.err_too_long").format(user=user, max=mm))
                    elif result == "ERR_COOLDOWN":
                         await ctx.send(gui.t("chat.err_cooldown").format(user=user))
                    else:
                        await ctx.send(gui.t("chat.err_not_found").format(user=user))

        self.twitch_bot = Bot()
        try: self.twitch_bot.run()
        except: pass

    def handle_request_sync(self, query, user):
        try:
            track = None
            if "track/" in query:
                track = self.sp_client.track(query)
            else:
                res = self.sp_client.search(q=query, limit=1, type='track')
                if res['tracks']['items']: track = res['tracks']['items'][0]
            if track:
                duration_ms = track['duration_ms']
                try: max_min = int(self.config_data.get('max_song_len_min', 10))
                except: max_min = 10
                if duration_ms > (max_min * 60 * 1000): return "ERR_TOO_LONG"
                
                name = f"{track['name']} - {track['artists'][0]['name']}"
                uri = track['uri']
                
                exists = next((x for x in self.queue_data if x['uri'] == uri), None)
                if exists:
                    if self.check_smart_var.get():
                         if user not in exists['reqs']:
                            exists['votes'] += 1
                            exists['reqs'].append(user)
                            self.log(self.t("logs.vote").format(name=name))
                            self.update_ui_safe()
                            return exists 
                         return exists 
                else: 
                    try: cd_min = int(self.config_data.get('song_cooldown_min', 30))
                    except: cd_min = 30
                    last_played = self.history_data.get(uri, 0)
                    if (time.time() - last_played) < (cd_min * 60): return "ERR_COOLDOWN"
                    
                    song_obj = {
                        'name': name, 'uri': uri, 
                        'votes': 1, 'reqs': [user],
                        'duration': duration_ms, 
                        'len_str': self.ms_to_min(duration_ms),
                        'is_manual': False
                    }
                    self.queue_data.append(song_obj)
                    self.history_data[uri] = time.time()
                    self.log(self.t("logs.new_song").format(name=name, user=user))
                    self.update_ui_safe()
                    return song_obj
            return None
        except Exception as e:
            self.log(f"Search Error: {e}")
            return None

    def ms_to_min(self, ms):
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def update_ui_safe(self):
        self.after(0, self.sort_and_update_ui)

if __name__ == "__main__":
    app = BotGUI()
    app.mainloop()
