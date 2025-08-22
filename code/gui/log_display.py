import tkinter as tk
from tkinter import Button, Checkbutton, Entry, Frame, BooleanVar, Label, filedialog, Canvas, Menu, messagebox
from tkinter import ttk
import threading
import queue
from datetime import datetime
import subprocess
import os
import sys
import webbrowser
import re
import copy
from pathlib import Path
import json
import shlex
import shutil

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

from .theme import load_themes
from .config import INTERPRETER_MAP, PAUSE_FLAG_PATH, DATA_DIR, SCRIPT_PATH, LOG_DIR
from .editor_window import EditorWindow
from .gui_widgets import StyledButton

SETTINGS_FILE = DATA_DIR / "gui_settings.json"

class LogDisplay(tk.Frame):
    """
    # The main GUI class for the Log Viewer.
    # 로그 뷰어의 메인 GUI 클래스입니다.
    """
    def __init__(self, master=None, script_path: str = "", log_dir: str = ""):
        self.themes = load_themes()
        self.custom_logs = self._load_custom_logs()
        self.filterable_log_types = [
            "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "COMMENT"
        ]
        self.filterable_log_types.extend(self.custom_logs.keys())

        self.script_path_var = tk.StringVar(value="")
        self.log_dir_var = tk.StringVar(value="")
        self.theme_name = tk.StringVar(value=list(self.themes.keys())[0])
        self.log_filter_vars = {
            log_type: BooleanVar(value=True) for log_type in self.filterable_log_types
        }
        
        self._load_settings()

        self.theme = self.themes[self.theme_name.get()]()
        self.theme.LOG_LEVEL_COLORS.update(self.custom_logs)

        super().__init__(master, bg=self.theme.BG_COLOR)
        self.master = master
        self.master.title("Glen Log Viewer")
        self.master.geometry("1200x850")
        self.master.configure(bg=self.theme.BG_COLOR)
        empty_menu = Menu(self.master); self.master.config(menu=empty_menu)
        self.pack(fill="both", expand=True)

        if DND_SUPPORT:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_drop)
            self.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.dnd_bind('<<DragLeave>>', self._on_drag_leave)
        
        if script_path and not self.script_path_var.get():
            self.script_path_var.set(script_path)
        if log_dir and not self.log_dir_var.get():
            self.log_dir_var.set(str(LOG_DIR))

        self.all_logs = []; self.undo_stack = []; self.redo_stack = []
        self.autocomplete_commands = {'/add': ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL"] + list(self.custom_logs.keys())}
        self.autocomplete_popup = None
        self.log_queue = queue.Queue()
        self.last_progress_message = None
        self.filter_button_text = tk.StringVar()
        self.filter_popup = None
        self.theme_popup = None
        self.is_running = False; self.is_paused = False; self.log_file_open = False
        self.think_core_process = None; self.current_log_file_path = None
        self.log_area_insert_index = None; self.selected_log_line_index = None; self.selected_log_abs_index = None
        self.log_font_size = 10; self.editor_window_instance = None
        self._animation_ids = {}
        self._is_resetting = False
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._perform_search_and_filter_logs())
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.case_sensitive_var.trace_add("write", lambda *args: self._perform_search_and_filter_logs())
        self.regex_var = tk.BooleanVar(value=False)
        self.regex_var.trace_add("write", lambda *args: self._perform_search_and_filter_logs())

        self.search_results = []
        self.current_search_index = -1
        self.is_full_screen_log = False
        
        self.create_widgets()
        self.configure_tags()
        self.update_ui_for_state()
        self._setup_global_shortcuts()

        auto_save = lambda *args: self._save_settings() if not self._is_resetting else None
        self.script_path_var.trace_add("write", auto_save)
        self.log_dir_var.trace_add("write", auto_save)
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_custom_logs(self):
        """
        # Loads custom log level definitions from a JSON file.
        # JSON 파일에서 사용자 정의 로그 레벨 정의를 로드합니다.
        """
        try:
            custom_log_file = DATA_DIR / "custom_logs.json"
            if custom_log_file.exists():
                with open(custom_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading custom_logs.json: {e}")
        return {}
    
    def _load_settings(self):
        """
        # Loads GUI settings from the settings file.
        # 설정 파일에서 GUI 설정을 로드합니다.
        """
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        self.script_path_var.set(settings.get("script_path", SCRIPT_PATH))
        self.log_dir_var.set(settings.get("log_dir", str(LOG_DIR)))
        self.theme_name.set(settings.get("theme", list(self.themes.keys())[0]))

        loaded_filters = settings.get("log_filters", {})
        for log_type, var in self.log_filter_vars.items():
            var.set(loaded_filters.get(log_type, True))
            
    def _save_settings(self):
        """
        # Saves the current GUI settings to the settings file.
        # 현재 GUI 설정을 설정 파일에 저장합니다.
        """
        settings = {
            "script_path": self.script_path_var.get(),
            "log_dir": self.log_dir_var.get(),
            "theme": self.theme_name.get(),
            "log_filters": {name: var.get() for name, var in self.log_filter_vars.items()}
        }
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def _reset_settings(self):
        """
        # Resets all settings to their default values after confirmation.
        # 확인 후 모든 설정을 기본값으로 재설정합니다.
        """
        if not messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to their defaults? This cannot be undone."):
            return
        
        self._is_resetting = True
        try:
            if os.path.exists(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)

            self.script_path_var.set(SCRIPT_PATH)
            self.log_dir_var.set(str(LOG_DIR))
            default_theme = list(self.themes.keys())[0]
            
            for var in self.log_filter_vars.values():
                var.set(True)

            self._on_theme_change(default_theme)
            self._perform_search_and_filter_logs(scroll_to_end=True)
            self.update_status("Settings have been reset to default.", self.theme.ACCENT_COLOR)
        finally:
            self._is_resetting = False

    def _on_closing(self):
        """
        # Handles the window closing event to save settings.
        # 창 닫기 이벤트를 처리하여 설정을 저장합니다.
        """
        self._save_settings()
        if self.editor_window_instance and self.editor_window_instance.winfo_exists():
            self.editor_window_instance.destroy()
        self.master.destroy()

    def _toggle_case_sensitivity(self):
        """
        # Toggles the case sensitivity option for searching.
        # 검색을 위한 대소문자 구분 옵션을 토글합니다.
        """
        self.case_sensitive_var.set(not self.case_sensitive_var.get())
        self._update_search_option_buttons_style()

    def _toggle_regex(self):
        """
        # Toggles the regular expression option for searching.
        # 검색을 위한 정규식 옵션을 토글합니다.
        """
        self.regex_var.set(not self.regex_var.get())
        self._update_search_option_buttons_style()

    def _update_search_option_buttons_style(self):
        """
        # Updates the visual style of search option buttons (Case, Regex) based on their state.
        # 검색 옵션 버튼(Case, Regex)의 상태에 따라 시각적 스타일을 업데이트합니다.
        """
        if self.case_sensitive_var.get():
            self.case_button.update_style(bg=self.theme.PRIMARY_COLOR, hover_color=self.theme.PRIMARY_HOVER_COLOR, fg=self.theme.BUTTON_STYLE['fg'])
        else:
            self.case_button.update_style(bg=self.theme.WIDGET_BG_COLOR, hover_color=self.theme.HOVER_COLOR, fg=self.theme.TEXT_COLOR)

        if self.regex_var.get():
            self.regex_button.update_style(bg=self.theme.PRIMARY_COLOR, hover_color=self.theme.PRIMARY_HOVER_COLOR, fg=self.theme.BUTTON_STYLE['fg'])
        else:
            self.regex_button.update_style(bg=self.theme.WIDGET_BG_COLOR, hover_color=self.theme.HOVER_COLOR, fg=self.theme.TEXT_COLOR)

    def get_all_log_levels(self) -> list:
        """
        # Returns a list of all standard and custom log levels.
        # 모든 표준 및 사용자 정의 로그 레벨 목록을 반환합니다.
        """
        return self.filterable_log_types
    
    def _setup_global_shortcuts(self):
        """
        # Sets up global keyboard shortcuts for the application.
        # 애플리케이션의 전역 키보드 단축키를 설정합니다.
        """
        self.master.bind_all("<Control-z>", lambda e: self._undo(1))
        self.master.bind_all("<Control-y>", lambda e: self._redo(1))
        self.master.bind_all("<Button-1>", self._on_global_click, add="+ ")
        self.master.bind_all("<Escape>", self._on_escape_key)

    def _on_escape_key(self, event=None):
        """
        # Handles the Escape key press, primarily to exit full-screen mode.
        # Escape 키 입력을 처리하며, 주로 전체 화면 모드를 종료하는 데 사용됩니다.
        """
        if self.is_full_screen_log:
            self._toggle_full_screen_log()

    def _animate_color(self, widget, start_color, end_color, duration=150, steps=15):
        """
        # Animates the background color of a widget.
        # 위젯의 배경색을 애니메이션으로 변경합니다.
        """
        widget_id = str(widget)
        if widget_id in self._animation_ids: self.master.after_cancel(self._animation_ids[widget_id])
        r1, g1, b1 = self.master.winfo_rgb(start_color); r2, g2, b2 = self.master.winfo_rgb(end_color)
        r_step, g_step, b_step = (r2 - r1) / steps, (g2 - g1) / steps, (b2 - b1) / steps
        delay = duration // steps
        def animate(step_num):
            if step_num < steps:
                r,g,b = int(r1+r_step*step_num), int(g1+g_step*step_num), int(b1+b_step*step_num)
                color = f"#{r>>8:02x}{g>>8:02x}{b>>8:02x}"
                try: widget.config(bg=color)
                except tk.TclError: pass
                self._animation_ids[widget_id] = self.master.after(delay, animate, step_num + 1)
            else:
                try: widget.config(bg=end_color)
                except tk.TclError: pass
                if widget_id in self._animation_ids: del self._animation_ids[widget_id]
        animate(0)

    def _animate_popup_fade_in(self, widget, start_alpha, end_alpha, duration, steps):
        """
        # Animates the fade-in of a Toplevel widget.
        # Toplevel 위젯의 페이드 인을 애니메이션으로 처리합니다.
        """
        alpha_step = (end_alpha - start_alpha) / steps
        delay = duration // steps
        def animate(step_num):
            if step_num < steps:
                alpha = start_alpha + alpha_step * step_num
                widget.attributes("-alpha", alpha)
                self.master.after(delay, animate, step_num + 1)
            else: widget.attributes("-alpha", end_alpha)
        animate(0)
    
    def create_widgets(self):
        """
        # Creates and lays out all the widgets in the main window.
        # 메인 창의 모든 위젯을 생성하고 배치합니다.
        """
        self.grid_rowconfigure(3, weight=1); self.grid_columnconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use('clam')
        
        self.config_frame = tk.LabelFrame(self, text="Configuration", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10, "bold"), padx=10, pady=10)
        self.config_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.config_frame.grid_columnconfigure(1, weight=1)

        Label(self.config_frame, text="Script Path:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.script_entry = Entry(self.config_frame, textvariable=self.script_path_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, font=(self.theme.FONT_FAMILY_UI, 9))
        self.script_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.script_browse_btn = StyledButton(self.config_frame, self, text="Browse...", command=self._browse_script_file,
            font=(self.theme.FONT_FAMILY_UI, 9), padx=8, pady=2,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.script_browse_btn.grid(row=0, column=2, padx=5, pady=5)

        Label(self.config_frame, text="Log Directory:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.log_dir_entry = Entry(self.config_frame, textvariable=self.log_dir_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, font=(self.theme.FONT_FAMILY_UI, 9))
        self.log_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.log_dir_browse_btn = StyledButton(self.config_frame, self, text="Browse...", command=self._browse_log_dir,
            font=(self.theme.FONT_FAMILY_UI, 9), padx=8, pady=2,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.log_dir_browse_btn.grid(row=1, column=2, padx=5, pady=5)

        Label(self.config_frame, text="Theme:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.theme_menu_button = StyledButton(self.config_frame, self, textvariable=self.theme_name,
            font=(self.theme.FONT_FAMILY_UI, 9),
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.theme_menu_button.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.theme_menu_button.bind("<Button-1>", self._toggle_theme_dropdown)

        self.filter_button = StyledButton(self.config_frame, self, textvariable=self.filter_button_text,
            font=(self.theme.FONT_FAMILY_UI, 10), padx=10, pady=5,
            bg=self.theme.FILTER_BUTTON_BG_COLOR, fg=self.theme.FILTER_BUTTON_FG_COLOR, hover_color=self.theme.FILTER_BUTTON_HOVER_BG_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.filter_button.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5,0), padx=5)
        self.filter_button.bind("<Button-1>", self._toggle_filter_dropdown)
        self._update_filter_button_text()
        
        self.reset_settings_btn = StyledButton(self.config_frame, self, text="Reset All Settings to Default", command=self._reset_settings,
            font=(self.theme.FONT_FAMILY_UI, 9), padx=8, pady=4,
            bg=self.theme.RESET_BUTTON_COLOR, fg=self.theme.BUTTON_STYLE['fg'], hover_color=self.theme.RESET_BUTTON_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.reset_settings_btn.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5))
        
        self.top_frame = Frame(self, bg=self.theme.BG_COLOR)
        self.top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        button_frame = Frame(self.top_frame, bg=self.theme.BG_COLOR)
        button_frame.pack(side="left", fill="x", expand=True)

        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        btn_kwargs = {'font': self.theme.BUTTON_STYLE['font'], 'fg': self.theme.BUTTON_STYLE['fg'], 'padx': 15, 'pady': 5}
        self.run_exit_button = StyledButton(button_frame, self, text="Run", command=self.toggle_run_exit, **btn_kwargs,
            bg=self.theme.SUCCESS_COLOR, hover_color=self.theme.SUCCESS_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.SUCCESS_HOVER_COLOR)
        self.run_exit_button.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.pause_resume_button = StyledButton(button_frame, self, text="Pause", command=self.toggle_pause_resume, **btn_kwargs,
            bg=self.theme.WARNING_COLOR, hover_color=self.theme.WARNING_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.WARNING_HOVER_COLOR)
        self.pause_resume_button.grid(row=0, column=1, padx=5, sticky="ew")

        self.open_log_folder_button = StyledButton(button_frame, self, text="Open Log Folder", command=self.open_log_folder, **btn_kwargs,
            bg=self.theme.PRIMARY_COLOR, hover_color=self.theme.PRIMARY_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.PRIMARY_HOVER_COLOR)
        self.open_log_folder_button.grid(row=0, column=2, padx=5, sticky="ew")

        self.open_log_file_button = StyledButton(button_frame, self, text="Open Log File", command=self.open_log_file, **btn_kwargs,
            bg=self.theme.SECONDARY_COLOR, hover_color=self.theme.SECONDARY_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.SECONDARY_HOVER_COLOR)
        self.open_log_file_button.grid(row=0, column=3, padx=5, sticky="ew")

        font_control_frame = Frame(self.top_frame, bg=self.theme.BG_COLOR)
        font_control_frame.pack(side="right", padx=5)
        
        font_btn_kwargs = {'font': (self.theme.FONT_FAMILY_UI, 9), 'padx': 5, 'pady': 1}
        
        self.toggle_view_btn = StyledButton(font_control_frame, self, text="⛶", command=self._toggle_full_screen_log, **font_btn_kwargs,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.toggle_view_btn.pack(side="right")
        
        self.font_increase_btn = StyledButton(font_control_frame, self, text="A+", command=self._increase_font_size, **font_btn_kwargs,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.font_increase_btn.pack(side="right", padx=(2,0))

        self.font_decrease_btn = StyledButton(font_control_frame, self, text="A-", command=self._decrease_font_size, **font_btn_kwargs,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.font_decrease_btn.pack(side="right")

        self.search_frame = Frame(self, bg=self.theme.BG_COLOR)
        self.search_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.search_frame.grid_columnconfigure(0, weight=1)

        search_main_frame = Frame(self.search_frame, bg=self.theme.BG_COLOR)
        search_main_frame.grid(row=0, column=0, sticky="ew")
        search_main_frame.grid_columnconfigure(1, weight=1)

        Label(search_main_frame, text="Search:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR).grid(row=0, column=0, padx=5)

        self.search_entry = Entry(search_main_frame, textvariable=self.search_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, font=(self.theme.FONT_FAMILY_UI, 10))
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, ipady=4)
        self.search_entry.bind("<Return>", self.next_match)
        self.search_entry.bind("<Shift-Return>", self.prev_match)

        nav_frame = Frame(search_main_frame, bg=self.theme.BG_COLOR)
        nav_frame.grid(row=0, column=2, padx=5)

        btn_kwargs = {'font': (self.theme.FONT_FAMILY_UI, 9), 'padx': 5, 'pady': 1,
                      'bg': self.theme.WIDGET_BG_COLOR, 'fg': self.theme.TEXT_COLOR, 'hover_color': self.theme.HOVER_COLOR,
                      'border_color': self.theme.BUTTON_BORDER_COLOR, 'hover_border_color': self.theme.ACCENT_COLOR}

        self.clear_search_btn = StyledButton(nav_frame, self, text="X", command=self._clear_search, **btn_kwargs)
        self.clear_search_btn.pack(side="left")

        self.case_button = StyledButton(nav_frame, self, text="Case", command=self._toggle_case_sensitivity, **btn_kwargs)
        self.case_button.pack(side="left", padx=(5, 0))

        self.regex_button = StyledButton(nav_frame, self, text="Regex", command=self._toggle_regex, **btn_kwargs)
        self.regex_button.pack(side="left", padx=(5, 0))

        self.prev_match_btn = StyledButton(nav_frame, self, text="<", command=self.prev_match, **btn_kwargs)
        self.prev_match_btn.pack(side="left", padx=(5, 0))

        self.search_count_label = Label(nav_frame, text="0/0", font=(self.theme.FONT_FAMILY_UI, 9), bg=self.theme.BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR, padx=4)
        self.search_count_label.pack(side="left")

        self.next_match_btn = StyledButton(nav_frame, self, text=">", command=self.next_match, **btn_kwargs)
        self.next_match_btn.pack(side="left")
        
        self.log_area_frame = Frame(self, bg=self.theme.BG_COLOR)
        self.log_area_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log_area_frame.grid_rowconfigure(0, weight=1)
        self.log_area_frame.grid_columnconfigure(0, weight=1)

        text_sub_frame = Frame(self.log_area_frame, bg=self.theme.LOG_AREA_BG_COLOR)
        text_sub_frame.grid(row=0, column=0, sticky="nsew")
        text_sub_frame.grid_rowconfigure(0, weight=1)
        text_sub_frame.grid_columnconfigure(0, weight=1)

        self.log_area = tk.Text(text_sub_frame, wrap=tk.WORD, state='disabled', font=(self.theme.FONT_FAMILY_LOG, self.log_font_size), bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, bd=0, highlightthickness=0, padx=5, pady=5)
        self.log_area.grid(row=0, column=0, sticky="nsew")
        self.log_area.bind("<Button-1>", self._handle_log_area_click)

        self.vsb = ttk.Scrollbar(text_sub_frame, orient="vertical", command=self.log_area.yview, style="Custom.Vertical.TScrollbar")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.log_area.config(yscrollcommand=self.vsb.set)
        
        self.progress_label = Label(self.log_area_frame, text="", font=(self.theme.FONT_FAMILY_LOG, self.log_font_size), bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.LOG_LEVEL_COLORS['PROGRESS'], anchor="w", padx=5)
        self.progress_label.grid(row=1, column=0, sticky="ew")

        self.restore_view_btn = StyledButton(self.log_area_frame, self, text="↓", command=self._toggle_full_screen_log,
            font=(self.theme.FONT_FAMILY_UI, 12, "bold"), padx=5, pady=0,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)

        bottom_frame = Frame(self, bg=self.theme.BG_COLOR)
        bottom_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.comment_container_frame = Frame(bottom_frame, bg=self.theme.ENTRY_BG_COLOR)
        self.comment_container_frame.grid(row=0, column=0, sticky="ew")
        self.comment_container_frame.grid_columnconfigure(1, weight=1)

        self.command_button = tk.Button(self.comment_container_frame, text="/", command=self._show_command_dropdown, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 12), relief="flat", activebackground=self.theme.WIDGET_BG_COLOR, activeforeground=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR, bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.command_button.grid(row=0, column=0, sticky="nsew")
        
        self.comment_entry = tk.Text(self.comment_container_frame, font=(self.theme.FONT_FAMILY_UI, 11), bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, highlightthickness=0, height=1, wrap="none", padx=10, pady=8)
        self.comment_entry.grid(row=0, column=1, sticky="ew")
        self.comment_entry.bind("<Return>", self.send_comment); self.comment_entry.bind("<Shift-Return>", "break")
        self.comment_entry.bind("<FocusIn>", self._on_comment_entry_focus_in); self.comment_entry.bind("<FocusOut>", self._on_comment_entry_focus_out)
        self.comment_entry.bind("<Key>", self._on_comment_entry_key_press); self.comment_entry.bind("<KeyRelease>", self._handle_autocomplete)

        self.send_button = tk.Button(self.comment_container_frame, text="➤", command=self.send_comment, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 14, "bold"), relief="flat", activebackground=self.theme.WIDGET_BG_COLOR, activeforeground=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR, bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.send_button.grid(row=0, column=2, sticky="nsew")
        
        self.command_button.bind("<Enter>", lambda e: self.on_entry_button_enter(self.command_button))
        self.command_button.bind("<Leave>", lambda e: self.on_entry_button_leave(self.command_button))
        self.send_button.bind("<Enter>", lambda e: self.on_entry_button_enter(self.send_button))
        self.send_button.bind("<Leave>", lambda e: self.on_entry_button_leave(self.send_button))

        status_frame = Frame(bottom_frame, bg=self.theme.BG_COLOR); status_frame.grid(row=1, column=0, sticky="e", padx=5, pady=(5,0))
        self.status_canvas = Canvas(status_frame, width=10, height=10, bg=self.theme.BG_COLOR, highlightthickness=0); self.status_canvas.pack(side="left", pady=2)
        self.status_label = Label(status_frame, text="Idle", font=(self.theme.FONT_FAMILY_UI, 9), bg=self.theme.BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR); self.status_label.pack(side="left", padx=(5,0))
        self.log_area.tag_bind("FILE_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("FILE_LINK", "<Leave>", self._on_link_leave)
        self.log_area.tag_bind("WEB_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("WEB_LINK", "<Leave>", self._on_link_leave)
        
        overlay_bg = getattr(self.theme, 'DROP_OVERLAY_BG_COLOR', self.theme.HIGHLIGHT_BG_COLOR)
        overlay_fg = getattr(self.theme, 'DROP_OVERLAY_FG_COLOR', self.theme.TEXT_COLOR)
        self.dnd_overlay = Label(self.master, text="Drop File or Folder Here",
                         bg=overlay_bg, fg=overlay_fg, font=(self.theme.FONT_FAMILY_UI, 24, "bold"))

        self.update_ui_for_state()

    def _toggle_full_screen_log(self):
        """
        # Toggles the log area between full-screen and normal view.
        # 로그 영역을 전체 화면과 일반 보기 사이에서 토글합니다.
        """
        self.is_full_screen_log = not self.is_full_screen_log
        if self.is_full_screen_log:
            self.config_frame.grid_remove()
            self.top_frame.grid_remove()
            self.search_frame.grid_remove()
            self.restore_view_btn.place(in_=self.log_area_frame, relx=1.0, rely=0, anchor='ne', x=-5, y=5)
        else:
            self.config_frame.grid()
            self.top_frame.grid()
            self.search_frame.grid()
            self.restore_view_btn.place_forget()

    def on_entry_button_enter(self, button):
        """
        # Handles mouse enter event for buttons in the comment entry area.
        # 댓글 입력 영역의 버튼에 대한 마우스 진입 이벤트를 처리합니다.
        """
        if button['state'] == 'normal':
            self._animate_color(button, self.theme.ENTRY_BG_COLOR, self.theme.WIDGET_BG_COLOR)

    def on_entry_button_leave(self, button):
        """
        # Handles mouse leave event for buttons in the comment entry area.
        # 댓글 입력 영역의 버튼에 대한 마우스 이탈 이벤트를 처리합니다.
        """
        if button['state'] == 'normal':
            self._animate_color(button, self.theme.WIDGET_BG_COLOR, self.theme.ENTRY_BG_COLOR)

    def _on_theme_change(self, theme_name: str):
        """
        # Handles theme change event.
        # 테마 변경 이벤트를 처리합니다.
        """
        self.theme_name.set(theme_name)
        new_theme_class = self.themes.get(theme_name)
        if new_theme_class:
            self.theme = new_theme_class()
            self.theme.LOG_LEVEL_COLORS.update(self.custom_logs)
            self._apply_theme()
            if self.editor_window_instance and self.editor_window_instance.winfo_exists():
                self.editor_window_instance._apply_theme()
            self._save_settings()

    def _apply_theme(self):
        """
        # Applies the currently selected theme to all relevant widgets.
        # 현재 선택된 테마를 모든 관련 위젯에 적용합니다.
        """
        self.master.configure(bg=self.theme.BG_COLOR)
        self.configure(bg=self.theme.BG_COLOR)

        def update_styles(widget):
            try:
                widget_class = widget.winfo_class()
                if widget_class in ('Frame', 'Label', 'Canvas', 'LabelFrame', 'TFrame'):
                    widget.configure(bg=self.theme.BG_COLOR)
                if widget_class in ('Label', 'LabelFrame', 'Button', 'Checkbutton'):
                     widget.configure(fg=self.theme.TEXT_COLOR)
            except tk.TclError: pass
            for child in widget.winfo_children(): update_styles(child)
        update_styles(self)
        
        style = ttk.Style()
        style.configure("Custom.Vertical.TScrollbar", gripcount=0, background=self.theme.WIDGET_BG_COLOR, darkcolor=self.theme.WIDGET_BG_COLOR, lightcolor=self.theme.WIDGET_BG_COLOR, troughcolor=self.theme.BG_COLOR, bordercolor=self.theme.BG_COLOR, relief="flat", arrowsize=0)
        style.map("Custom.Vertical.TScrollbar", background=[('active', self.theme.ACCENT_COLOR), ('!disabled', self.theme.WIDGET_BG_COLOR)], relief=[('pressed', 'sunken'), ('!pressed', 'flat')])

        if hasattr(self, 'dnd_overlay'):
            overlay_bg = getattr(self.theme, 'DROP_OVERLAY_BG_COLOR', self.theme.HIGHLIGHT_BG_COLOR)
            overlay_fg = getattr(self.theme, 'DROP_OVERLAY_FG_COLOR', self.theme.TEXT_COLOR)
            self.dnd_overlay.configure(bg=overlay_bg, fg=overlay_fg)
        
        self.config_frame.configure(bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR)
        self.script_entry.configure(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)
        self.log_dir_entry.configure(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)
        self.search_entry.configure(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)

        widget_btn_theme = {'font': (self.theme.FONT_FAMILY_UI, 9), 
            'bg': self.theme.WIDGET_BG_COLOR, 'fg': self.theme.TEXT_COLOR, 'hover_color': self.theme.HOVER_COLOR,
            'border_color': self.theme.BUTTON_BORDER_COLOR, 'hover_border_color': self.theme.ACCENT_COLOR}
        self.script_browse_btn.update_style(**widget_btn_theme)
        self.log_dir_browse_btn.update_style(**widget_btn_theme)
        self.font_increase_btn.update_style(**widget_btn_theme)
        self.font_decrease_btn.update_style(**widget_btn_theme)
        self.toggle_view_btn.update_style(**widget_btn_theme)
        self.theme_menu_button.update_style(**widget_btn_theme)
        self.clear_search_btn.update_style(**widget_btn_theme)
        self.prev_match_btn.update_style(**widget_btn_theme)
        self.next_match_btn.update_style(**widget_btn_theme)
        self._update_search_option_buttons_style()
        
        self.filter_button.update_style(
            bg=self.theme.FILTER_BUTTON_BG_COLOR, fg=self.theme.FILTER_BUTTON_FG_COLOR, hover_color=self.theme.FILTER_BUTTON_HOVER_BG_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        
        self.reset_settings_btn.update_style(
            bg=self.theme.RESET_BUTTON_COLOR, fg=self.theme.BUTTON_STYLE['fg'], hover_color=self.theme.RESET_BUTTON_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR
        )
        
        self.command_button.config(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, activebackground=self.theme.WIDGET_BG_COLOR, activeforeground=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR)
        self.send_button.config(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, activebackground=self.theme.WIDGET_BG_COLOR, activeforeground=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR)

        self.log_area.configure(bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)
        self.progress_label.configure(bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.LOG_LEVEL_COLORS['PROGRESS'])
        self.comment_container_frame.configure(bg=self.theme.ENTRY_BG_COLOR)
        self.comment_entry.configure(bg=self.theme.ENTRY_BG_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)
        self.status_label.configure(bg=self.theme.BG_COLOR)
        self.status_canvas.configure(bg=self.theme.BG_COLOR)
        self.status_label.configure(fg=self.theme.DISABLED_TEXT_COLOR)
        
        self.update_ui_for_state()
        self.configure_tags()
        self._perform_search_and_filter_logs()
        if self.editor_window_instance and self.editor_window_instance.winfo_exists():
            self.editor_window_instance.destroy()
            self.open_editor_window()

    def _is_restricted_folder(self, path: str) -> bool:
        """
        # Checks if a given path is a restricted system folder.
        # 주어진 경로가 제한된 시스템 폴더인지 확인합니다.
        """
        try:
            norm_path = Path(path).resolve()
            gui_dir = Path(__file__).parent.resolve()
            if gui_dir == norm_path or gui_dir in norm_path.parents: return True
            system_roots = [
                Path(os.environ.get("SystemRoot", "C:\\Windows")).resolve(),
                Path(os.environ.get("ProgramFiles", "C:\\Program Files")).resolve(),
                Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")).resolve(),
            ]
            user_profile = Path(os.environ.get("UserProfile", ""))
            if user_profile.exists(): system_roots.append(user_profile.resolve().parent) 
            for root in system_roots:
                if norm_path == root or root in norm_path.parents: return True
        except Exception as e:
            self.update_status(f"Path check error: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return True 
        return False

    def _on_drag_enter(self, event):
        """
        # Shows an overlay when a file is dragged over the window.
        # 파일이 창 위로 드래그될 때 오버레이를 표시합니다.
        """
        self.dnd_overlay.place(in_=self.master, relx=0, rely=0, relwidth=1, relheight=1)
        self.dnd_overlay.lift()

    def _on_drag_leave(self, event):
        """
        # Hides the overlay when a dragged file leaves the window area.
        # 드래그된 파일이 창 영역을 벗어날 때 오버레이를 숨깁니다.
        """
        self.dnd_overlay.place_forget()

    def _on_drop(self, event):
        """
        # Handles files dropped onto the window.
        # 창에 드롭된 파일을 처리합니다.
        """
        self.dnd_overlay.place_forget()
        try:
            paths = self.master.tk.splitlist(event.data)
        except (tk.TclError, AttributeError):
            paths = event.data.strip().replace("{", "").replace("}", "").split()
        if not paths:
            return
        path = paths[0]
        if os.path.isfile(path):
            if path.lower().endswith(".log"):
                self._load_log_file(path)
            else:
                self.script_path_var.set(path)
                self.update_status(f"Script path set to: {os.path.basename(path)}", self.theme.PRIMARY_COLOR)
        elif os.path.isdir(path):
            if self._is_restricted_folder(path):
                messagebox.showwarning("Restricted Folder", f"This folder is restricted and cannot be used as a log directory:\n\n{path}")
                self.update_status(f"Cannot use restricted folder: {path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            else:
                self.log_dir_var.set(path)
                self.update_status(f"Log directory set to: {os.path.basename(path)}", self.theme.PRIMARY_COLOR)

    def _on_global_click(self, event):
        """
        # Handles global mouse clicks to close popups like filters or themes.
        # 전역 마우스 클릭을 처리하여 필터나 테마 같은 팝업을 닫습니다.
        """
        widget_under_cursor = self.winfo_containing(event.x_root, event.y_root)
        
        def is_click_outside(popup_widget, button_widget):
            if not popup_widget or not popup_widget.winfo_exists():
                return False
            w = widget_under_cursor
            while w:
                if w == popup_widget or w == button_widget:
                    return False
                try: w = w.master
                except Exception: break
            return True

        if is_click_outside(self.filter_popup, self.filter_button):
            self._close_filter_dropdown()

        if is_click_outside(self.theme_popup, self.theme_menu_button):
            self._close_theme_dropdown()

        if is_click_outside(self.autocomplete_popup, self.comment_entry):
            self._close_autocomplete_popup()

    def _update_filter_button_text(self):
        """
        # Updates the text on the filter button to show the current filter status.
        # 필터 버튼의 텍스트를 업데이트하여 현재 필터 상태를 표시합니다.
        """
        enabled_count = sum(1 for var in self.log_filter_vars.values() if var.get())
        total_count = len(self.log_filter_vars)
        all_enabled = enabled_count == total_count
        is_open = self.filter_popup and self.filter_popup.winfo_exists()
        arrow = "▲" if is_open else "▼"
        self.filter_button_text.set(f"Filters ({'All' if all_enabled else f'{enabled_count}/{total_count}'}) {arrow}")

    def _close_filter_dropdown(self, event=None):
        """
        # Closes the filter selection dropdown.
        # 필터 선택 드롭다운을 닫습니다.
        """
        if self.filter_popup and self.filter_popup.winfo_exists():
            self.filter_popup.destroy()
            self.filter_popup = None
        self._update_filter_button_text()
    
    def _close_theme_dropdown(self, event=None):
        """
        # Closes the theme selection dropdown.
        # 테마 선택 드롭다운을 닫습니다.
        """
        if self.theme_popup and self.theme_popup.winfo_exists():
            self.theme_popup.destroy()
            self.theme_popup = None

    def _close_autocomplete_popup(self, event=None):
        """
        # Closes the command autocomplete popup.
        # 명령어 자동완성 팝업을 닫습니다.
        """
        if self.autocomplete_popup and self.autocomplete_popup.winfo_exists():
            self.autocomplete_popup.destroy()
            self.autocomplete_popup = None

    def _toggle_theme_dropdown(self, event):
        """
        # Toggles the visibility of the theme selection dropdown.
        # 테마 선택 드롭다운의 가시성을 토글합니다.
        """
        if self.theme_popup and self.theme_popup.winfo_exists():
            self._close_theme_dropdown()
            return
        
        self.theme_popup = popup = tk.Toplevel(self.master)
        popup.wm_overrideredirect(True)
        popup.wm_transient(self.master)
        popup.bind("<FocusOut>", self._close_theme_dropdown)

        button_widget = self.theme_menu_button
        x = button_widget.winfo_rootx()
        y = button_widget.winfo_rooty() + button_widget.winfo_height() + 2
        width = button_widget.winfo_width()

        DROPDOWN_BG_COLOR = getattr(self.theme, 'DROPDOWN_BG_COLOR', self.theme.WIDGET_BG_COLOR)
        DROPDOWN_BORDER_COLOR = getattr(self.theme, 'DROPDOWN_BORDER_COLOR', self.theme.ACCENT_COLOR)
        DROPDOWN_HOVER_BG_COLOR = getattr(self.theme, 'DROPDOWN_HOVER_BG_COLOR', self.theme.PRIMARY_HOVER_COLOR)

        main_frame = Frame(popup, bg=DROPDOWN_BG_COLOR, highlightbackground=DROPDOWN_BORDER_COLOR, highlightthickness=1)
        main_frame.pack(fill='both', expand=True)

        for theme_name in self.themes.keys():
            container = Frame(main_frame, bg=DROPDOWN_BG_COLOR)
            container.pack(fill='x', expand=True, padx=1, pady=1)
            
            is_selected = theme_name == self.theme_name.get()
            
            label = Label(container, text=theme_name,
                          bg=DROPDOWN_HOVER_BG_COLOR if is_selected else DROPDOWN_BG_COLOR,
                          fg=self.theme.TEXT_COLOR,
                          font=(self.theme.FONT_FAMILY_UI, 9, "bold" if is_selected else "normal"),
                          anchor="w", cursor="hand2", padx=10, pady=4)
            label.pack(fill='x', expand=True)

            def create_click_handler(name):
                return lambda e: (self._on_theme_change(name), self._close_theme_dropdown())

            def create_hover_bindings(c, lbl, selected):
                def on_enter(e):
                    if not selected:
                        c.config(bg=DROPDOWN_HOVER_BG_COLOR)
                        lbl.config(bg=DROPDOWN_HOVER_BG_COLOR)
                def on_leave(e):
                    if not selected:
                        c.config(bg=DROPDOWN_BG_COLOR)
                        lbl.config(bg=DROPDOWN_BG_COLOR)
                return on_enter, on_leave

            label.bind("<Button-1>", create_click_handler(theme_name))
            enter_func, leave_func = create_hover_bindings(container, label, is_selected)
            container.bind("<Enter>", enter_func); container.bind("<Leave>", leave_func)
            label.bind("<Enter>", enter_func); label.bind("<Leave>", leave_func)
        
        popup.update_idletasks()
        popup_height = popup.winfo_height()
        popup.geometry(f"{width}x{popup_height}+{x}+{y}")
        popup.attributes("-alpha", 0)
        popup.deiconify()
        self._animate_popup_fade_in(popup, 0.0, 1.0, duration=100, steps=10)
        popup.focus_set()

    def _toggle_filter_dropdown(self, event):
        """
        # Toggles the visibility of the log level filter dropdown.
        # 로그 레벨 필터 드롭다운의 가시성을 토글합니다.
        """
        if self.filter_popup and self.filter_popup.winfo_exists():
            self._close_filter_dropdown()
            return
            
        self.filter_popup = popup = tk.Toplevel(self.master)
        popup.wm_overrideredirect(True)
        popup.wm_transient(self.master)
        popup.bind("<FocusOut>", self._close_filter_dropdown)

        button_widget = event.widget
        x = button_widget.winfo_rootx()
        y = button_widget.winfo_rooty() + button_widget.winfo_height() + 2

        DROPDOWN_BG_COLOR = getattr(self.theme, 'DROPDOWN_BG_COLOR', self.theme.WIDGET_BG_COLOR)
        DROPDOWN_BORDER_COLOR = getattr(self.theme, 'DROPDOWN_BORDER_COLOR', self.theme.ACCENT_COLOR)
        DROPDOWN_HOVER_BG_COLOR = getattr(self.theme, 'DROPDOWN_HOVER_BG_COLOR', self.theme.PRIMARY_HOVER_COLOR)

        main_frame = Frame(popup, bg=DROPDOWN_BG_COLOR, highlightbackground=DROPDOWN_BORDER_COLOR, highlightthickness=1)
        main_frame.pack()

        controls_frame = Frame(main_frame, bg=DROPDOWN_BG_COLOR)
        controls_frame.pack(fill='x', padx=10, pady=(10, 5))

        def select_all(select=True):
            for var in self.log_filter_vars.values(): var.set(select)
            self._perform_search_and_filter_logs()

        all_button = tk.Button(controls_frame, text="Select All", command=lambda: select_all(True), bg=DROPDOWN_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", font=(self.theme.FONT_FAMILY_UI, 9), activebackground=DROPDOWN_HOVER_BG_COLOR)
        all_button.pack(side="left", padx=(5,0))
        all_button.bind("<Enter>", lambda e, w=all_button: self._animate_color(w, DROPDOWN_BG_COLOR, DROPDOWN_HOVER_BG_COLOR))
        all_button.bind("<Leave>", lambda e, w=all_button: self._animate_color(w, DROPDOWN_HOVER_BG_COLOR, DROPDOWN_BG_COLOR))

        none_button = tk.Button(controls_frame, text="Deselect All", command=lambda: select_all(False), bg=DROPDOWN_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", font=(self.theme.FONT_FAMILY_UI, 9), activebackground=DROPDOWN_HOVER_BG_COLOR)
        none_button.pack(side="left", padx=5)
        none_button.bind("<Enter>", lambda e, w=none_button: self._animate_color(w, DROPDOWN_BG_COLOR, DROPDOWN_HOVER_BG_COLOR))
        none_button.bind("<Leave>", lambda e, w=none_button: self._animate_color(w, DROPDOWN_HOVER_BG_COLOR, DROPDOWN_BG_COLOR))
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', padx=5, pady=5)
        
        check_frame = Frame(main_frame, bg=DROPDOWN_BG_COLOR, padx=5)
        check_frame.pack(pady=(0, 5))

        num_cols = 2
        for i, log_type in enumerate(self.filterable_log_types):
            var = self.log_filter_vars[log_type]
            chk_color = self.theme.LOG_LEVEL_COLORS.get(log_type, self.theme.TEXT_COLOR)
            
            container = Frame(check_frame, bg=DROPDOWN_BG_COLOR)
            chk = Checkbutton(container, text=log_type, variable=var, command=self._perform_search_and_filter_logs,
                              bg=DROPDOWN_BG_COLOR, fg=chk_color, selectcolor=self.theme.ENTRY_BG_COLOR,
                              font=(self.theme.FONT_FAMILY_UI, 9, "bold"), bd=0, highlightthickness=0,
                              activebackground=DROPDOWN_BG_COLOR, activeforeground=chk_color,
                              anchor="w", cursor="hand2", padx=10, pady=4)
            chk.pack(fill='x', expand=True)
            container.grid(row=i // num_cols, column=i % num_cols, sticky="ew", padx=5, pady=1)
            
            def create_hover_bindings(c, chk_widget):
                def on_enter(e):
                    c.config(bg=DROPDOWN_HOVER_BG_COLOR)
                    chk_widget.config(bg=DROPDOWN_HOVER_BG_COLOR, activebackground=DROPDOWN_HOVER_BG_COLOR)
                def on_leave(e):
                    c.config(bg=DROPDOWN_BG_COLOR)
                    chk_widget.config(bg=DROPDOWN_BG_COLOR, activebackground=DROPDOWN_BG_COLOR)
                return on_enter, on_leave

            enter_func, leave_func = create_hover_bindings(container, chk)
            container.bind("<Enter>", enter_func); container.bind("<Leave>", leave_func)
            chk.bind("<Enter>", enter_func); chk.bind("<Leave>", leave_func)
        
        popup.update_idletasks()
        
        popup.geometry(f"+{x}+{y}")
        popup.attributes("-alpha", 0)
        popup.deiconify()
        self._animate_popup_fade_in(popup, 0.0, 1.0, duration=100, steps=10)
        popup.focus_set()
        self._update_filter_button_text()

    def _clear_search(self):
        """
        # Clears the search bar and removes all search highlights.
        # 검색창을 비우고 모든 검색 하이라이트를 제거합니다.
        """
        self.search_var.set("")
        self.log_area.tag_remove("search_highlight", '1.0', tk.END)
        self.log_area.tag_remove("current_search_highlight", '1.0', tk.END)
        self.search_results = []
        self.current_search_index = -1
        self.search_count_label.config(text="0/0")

    def next_match(self, event=None):
        """
        # Navigates to the next search result.
        # 다음 검색 결과로 이동합니다.
        """
        if not self.search_results:
            return "break"
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self._update_search_highlight()
        return "break"

    def prev_match(self, event=None):
        """
        # Navigates to the previous search result.
        # 이전 검색 결과로 이동합니다.
        """
        if not self.search_results:
            return "break"
        self.current_search_index = (self.current_search_index - 1 + len(self.search_results)) % len(self.search_results)
        self._update_search_highlight()
        return "break"

    def _update_search_highlight(self):
        """
        # Highlights the current search match in the log area.
        # 로그 영역에서 현재 검색 결과를 하이라이트합니다.
        """
        self.log_area.tag_remove("current_search_highlight", "1.0", tk.END)
        if not self.search_results or self.current_search_index < 0:
            return

        result = self.search_results[self.current_search_index]
        start_index, end_index = result['start'], result['end']
        
        self.log_area.tag_add("current_search_highlight", start_index, end_index)
        self.log_area.see(start_index)
        
        self.search_count_label.config(text=f"{self.current_search_index + 1}/{len(self.search_results)}")

    def _perform_search_and_filter_logs(self, scroll_to_end=False):
        """
        # Refreshes the log display based on current filters and search terms.
        # 현재 필터 및 검색어에 따라 로그 표시를 새로 고칩니다.
        """
        self._update_filter_button_text()
        
        self.log_area.tag_remove("search_highlight", '1.0', tk.END)
        self.log_area.tag_remove("current_search_highlight", '1.0', tk.END)
        self.search_results = []
        self.current_search_index = -1

        current_scroll_fraction = self.log_area.yview()[0]
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)

        search_term = self.search_var.get()
        search_flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE
        use_regex = self.regex_var.get()

        temp_search_results = []

        for i, log_entry in enumerate(self.all_logs):
            level = log_entry.get('level', 'INFO')
            is_filterable = level in self.filterable_log_types
            level_should_display = not is_filterable or self.log_filter_vars.get(level, BooleanVar(value=True)).get()

            if log_entry.get('state') != 'DELETED' and level_should_display:
                base_tags = list(self._get_tags_for_log(log_entry)) + [f"log_index_{i}"]
                log_message = log_entry['message']
                links = self._find_links_in_text(log_message)

                if not links:
                    self.log_area.insert(tk.END, log_message + '\n', tuple(base_tags))
                else:
                    last_index = 0
                    sorted_links = sorted(links, key=lambda l: l[1])
                    for link_type, link_start, link_end in sorted_links:
                        plain_text = log_message[last_index:link_start]
                        if plain_text:
                            self.log_area.insert(tk.END, plain_text, tuple(base_tags))
                        link_text = log_message[link_start:link_end]
                        link_tags = tuple(base_tags + [link_type])
                        self.log_area.insert(tk.END, link_text, link_tags)
                        last_index = link_end
                    remaining_text = log_message[last_index:]
                    if remaining_text:
                        self.log_area.insert(tk.END, remaining_text, tuple(base_tags))
                    self.log_area.insert(tk.END, '\n')

                if search_term:
                    line_start_index = self.log_area.index(f"end-2c linestart")
                    try:
                        if use_regex:
                            for match in re.finditer(search_term, log_message, search_flags):
                                start, end = match.span()
                                temp_search_results.append({
                                    'start': f"{line_start_index}+{start}c",
                                    'end': f"{line_start_index}+{end}c"
                                })
                        else:
                            start = 0
                            while True:
                                start = log_message.lower().find(search_term.lower(), start) if not self.case_sensitive_var.get() else log_message.find(search_term, start)
                                if start == -1: break
                                end = start + len(search_term)
                                temp_search_results.append({
                                    'start': f"{line_start_index}+{start}c",
                                    'end': f"{line_start_index}+{end}c"
                                })
                                start += 1
                    except re.error as e:
                        self.update_status(f"Regex Error: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                        pass

        for result in temp_search_results:
            self.log_area.tag_add("search_highlight", result['start'], result['end'])
        
        self.search_results = temp_search_results
        self.log_area.configure(state='disabled')

        if scroll_to_end:
            self.log_area.yview_moveto(1.0)
        else:
            self.log_area.yview_moveto(current_scroll_fraction)

        if self.search_results:
            self.current_search_index = 0
            self._update_search_highlight()
        else:
            self.search_count_label.config(text="0/0")
                
    def _browse_script_file(self):
        """
        # Opens a file dialog to select a script file.
        # 스크립트 파일을 선택하기 위한 파일 대화상자를 엽니다.
        """
        filepath = filedialog.askopenfilename(
            title="Select script to run",
            filetypes=(("All files", "*.*"),)
        )
        if filepath:
            self.script_path_var.set(filepath)
            self.update_status(f"Script path set to: {os.path.basename(filepath)}", self.theme.PRIMARY_COLOR)
            self.update_status(f"Script path set to: {os.path.basename(filepath)}", self.theme.PRIMARY_COLOR)

    def _browse_log_dir(self):
        """
        # Opens a directory dialog to select a log directory.
        # 로그 디렉토리를 선택하기 위한 디렉토리 대화상자를 엽니다.
        """
        dirpath = filedialog.askdirectory(title="Select folder to save logs")
        if dirpath:
            self.log_dir_var.set(dirpath)
            self.update_status(f"Log directory set to: {os.path.basename(dirpath)}", self.theme.PRIMARY_COLOR)
            self.update_status(f"Log directory set to: {os.path.basename(dirpath)}", self.theme.PRIMARY_COLOR)
            self.update_status(f"Log directory set to: {os.path.basename(dirpath)}", self.theme.PRIMARY_COLOR)
            
    def _on_link_enter(self, event):
        """
        # Changes the cursor to a hand when hovering over a link.
        # 링크 위에 마우스를 올리면 커서를 손 모양으로 변경합니다.
        """
        self.log_area.config(cursor="hand2")

    def _on_link_leave(self, event):
        """
        # Reverts the cursor when leaving a link.
        # 링크에서 마우스를 떼면 커서를 원래대로 되돌립니다.
        """
        self.log_area.config(cursor="")

    def _handle_log_area_click(self, event):
        """
        # Handles all click events in the log area, including link clicks and line selection.
        # 링크 클릭 및 라인 선택을 포함하여 로그 영역의 모든 클릭 이벤트를 처리합니다.
        """
        index = self.log_area.index(f"@{event.x},{event.y}")
        tags = self.log_area.tag_names(index)
        
        is_ctrl = (event.state & 0x4) != 0
        is_shift = (event.state & 0x1) != 0

        link_type = None
        if "FILE_LINK" in tags:
            link_type = "FILE_LINK"
        elif "WEB_LINK" in tags:
            link_type = "WEB_LINK"

        if link_type and is_ctrl:
            tag_range = self.log_area.tag_prevrange(link_type, index)
            link_text = self.log_area.get(tag_range[0], tag_range[1]).strip('"')
            if link_type == "WEB_LINK":
                try:
                    webbrowser.open_new_tab(link_text)
                    self.update_status(f"Opened web page: {link_text}", self.theme.ACCENT_COLOR)
                except Exception as e:
                    self.update_status(f"Error opening web page: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            elif link_type == "FILE_LINK":
                file_path = link_text.lstrip('@')
                try:
                    os.startfile(os.path.normpath(file_path))
                    self.update_status(f"Opened file: {os.path.basename(file_path)}", self.theme.ACCENT_COLOR)
                except Exception as e:
                    self.update_status(f"Error opening file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return "break"

        if link_type == "FILE_LINK" and is_shift:
            tag_range = self.log_area.tag_prevrange("FILE_LINK", index)
            link_text = self.log_area.get(tag_range[0], tag_range[1]).strip('"')
            file_path = link_text.lstrip('@')
            dir_path = os.path.dirname(os.path.normpath(file_path))
            if os.path.isdir(dir_path):
                try:
                    os.startfile(dir_path)
                    self.update_status(f"Opened folder: {dir_path}", self.theme.ACCENT_COLOR)
                except Exception as e:
                    self.update_status(f"Error opening folder: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            else:
                self.update_status(f"Folder not found: {dir_path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return "break"

        is_editable = (self.is_running and self.is_paused) or not self.is_running
        if not is_editable or link_type:
            return

        clicked_index = self.log_area.index(f"@{event.x},{event.y}")
        line_start = clicked_index.split('.')[0] + '.0'
        if self.selected_log_line_index == line_start or not self.log_area.get(line_start, f"{line_start} lineend").strip():
            self.selected_log_line_index = self.selected_log_abs_index = self.log_area_insert_index = None
            self._normalize_all_logs(scroll_to_end=False)
            if self.editor_window_instance and self.editor_window_instance.winfo_exists():
                self.editor_window_instance.update_content(None)
        else:
            tags = self.log_area.tag_names(line_start)
            abs_index = None
            for tag in tags:
                if tag.startswith("log_index_"):
                    try:
                        abs_index = int(tag.split('_')[-1])
                        break
                    except (ValueError, IndexError):
                        continue
            if abs_index is None: return
            self._normalize_all_logs(scroll_to_end=False)
            self.log_area.tag_add("highlight", line_start, f"{line_start} lineend")
            self.log_area_insert_index = f"{line_start} lineend"
            self.selected_log_line_index = line_start
            self.selected_log_abs_index = abs_index
            self.update_status(f"Selected line {int(line_start.split('.')[0])}", self.theme.ACCENT_COLOR)
            if self.editor_window_instance and self.editor_window_instance.winfo_exists():
                self.editor_window_instance.update_content(self.selected_log_abs_index)

    def _on_comment_entry_focus_in(self, event):
        """
        # Handles the focus-in event for the comment entry box.
        # 댓글 입력 상자의 포커스 인 이벤트를 처리합니다.
        """
        if self.comment_entry['state'] == 'disabled': return
        current_text = self.comment_entry.get(1.0, tk.END).strip()
        if current_text.startswith("Editing is only") or current_text.startswith("Idle:"): self.comment_entry.delete(1.0, tk.END)
        self.comment_entry.config(fg=self.theme.TEXT_COLOR)

    def _on_comment_entry_focus_out(self, event):
        """
        # Handles the focus-out event for the comment entry box.
        # 댓글 입력 상자의 포커스 아웃 이벤트를 처리합니다.
        """
        if self.comment_entry['state'] == 'disabled' or not self.winfo_exists():
            return
        if not self.comment_entry.get(1.0, tk.END).strip():
            self.update_ui_for_state()
            
    def _on_comment_entry_key_press(self, event):
        """
        # Handles key press events in the comment entry, like the Ctrl+E shortcut for the editor.
        # 댓글 입력창의 키 입력 이벤트를 처리합니다. (예: 에디터 창을 여는 Ctrl+E)
        """
        if self.comment_entry['state'] == 'disabled': return "break"
        is_editable = (self.is_running and self.is_paused) or not self.is_running
        if event.state & 0x4 and event.keysym.lower() == 'e' and is_editable: self.open_editor_window(); return "break"
        
    def open_editor_window(self):
        """
        # Opens the log editor window, or brings it to the front if already open.
        # 로그 에디터 창을 열거나, 이미 열려있으면 앞으로 가져옵니다.
        """
        if self.editor_window_instance and self.editor_window_instance.winfo_exists(): 
            self.editor_window_instance.lift()
            self.editor_window_instance.focus_set()
            return
        
        self.editor_window_instance = EditorWindow(self, self.selected_log_abs_index)
        
        self.master.update_idletasks()
        main_win_x = self.master.winfo_rootx()
        main_win_y = self.master.winfo_rooty()
        main_win_w = self.master.winfo_width()
        main_win_h = self.master.winfo_height()
        
        editor_w = 800
        editor_h = 600
        
        pos_x = main_win_x + (main_win_w // 2) - (editor_w // 2)
        pos_y = main_win_y + (main_win_h // 2) - (editor_h // 2)
        
        self.editor_window_instance.geometry(f"{editor_w}x{editor_h}+{pos_x}+{pos_y}")

    def _normalize_all_logs(self, scroll_to_end=True):
        """
        # Helper function to redraw all logs based on current filters and search.
        # 현재 필터와 검색에 따라 모든 로그를 다시 그리는 헬퍼 함수입니다.
        """
        self._perform_search_and_filter_logs(scroll_to_end=scroll_to_end)

    def configure_tags(self):
        """
        # Configures text tags for syntax highlighting of different log levels.
        # 다양한 로그 레벨의 구문 강조를 위한 텍스트 태그를 구성합니다.
        """
        base_font = (self.theme.FONT_FAMILY_LOG, self.log_font_size)
        self.log_area.config(font=base_font)
        for level, color in self.theme.LOG_LEVEL_COLORS.items():
            font_config = list(base_font)
            extra_config = {}
            if level == "FATAL": font_config.extend(["bold"])
            elif level in ["COMMENT", "ADDED", "MODIFIED"] or level in self.custom_logs: 
                font_config.extend(["italic"])
            elif level == "DELETED": extra_config["overstrike"] = True
            self.log_area.tag_config(level, foreground=color, font=tuple(font_config), **extra_config)
        self.log_area.tag_config("highlight", background=self.theme.HIGHLIGHT_BG_COLOR, foreground=self.theme.HIGHLIGHT_FG_COLOR)
        self.log_area.tag_config("FILE_LINK", foreground=self.theme.LINK_COLOR, underline=True)
        self.log_area.tag_config("WEB_LINK", foreground=self.theme.LINK_COLOR, underline=True)
        highlight_bg = getattr(self.theme, 'SEARCH_HIGHLIGHT_BG', '#f0e68c')
        highlight_fg = getattr(self.theme, 'SEARCH_HIGHLIGHT_FG', '#000000')
        self.log_area.tag_config("search_highlight", background=highlight_bg, foreground=highlight_fg)
        self.log_area.tag_config("current_search_highlight", background=self.theme.ACCENT_COLOR, foreground=self.theme.BG_COLOR)

    def _get_tags_for_log(self, log_entry):
        """
        # Gets the appropriate tags for a given log entry based on its level and state.
        # 주어진 로그 항목의 레벨과 상태에 따라 적절한 태그를 가져옵니다.
        """
        tags = [log_entry.get('level', 'INFO')]
        if 'state' in log_entry and log_entry['state'] != 'SAVED': tags.append(log_entry['state'])
        return tuple(tags)

    def _find_links_in_text(self, line_text):
        """
        # Finds file and web links in a string and returns their details.
        # 문자열에서 파일 및 웹 링크를 찾아 상세 정보를 반환합니다.
        """
        links = []
        path_regex = r'(@(?:"[a-zA-Z]:[\\/][^"\n]*"|\[[^"\n]+\]|[a-zA-Z]:[\\/][^\s<>"\n]*|\\[^\s<>"\n]+))'
        web_regex = r'(https?://[^\s<>"\n]+)'

        for match in re.finditer(path_regex, line_text):
            links.append(("FILE_LINK", match.start(), match.end()))

        for match in re.finditer(web_regex, line_text):
            links.append(("WEB_LINK", match.start(), match.end()))
        
        return links
                
    def add_log(self, message, level='INFO', to_file=True, scroll=True):
        """
        # Adds a log entry to the display and optionally to the log file.
        # 로그 항목을 화면에 추가하고, 선택적으로 로그 파일에도 기록합니다.
        """
        log_entry = {'message': message, 'level': level, 'state': 'SAVED'}
        self.all_logs.append(log_entry)
        
        is_filterable = level in self.filterable_log_types
        should_display_level = not is_filterable or self.log_filter_vars.get(level, BooleanVar(value=True)).get()
        
        if should_display_level:
            self.log_area.config(state='normal')
            i = len(self.all_logs) - 1
            base_tags = list(self._get_tags_for_log(log_entry)) + [f"log_index_{i}"]
            links = self._find_links_in_text(log_entry['message'])

            if not links:
                self.log_area.insert(tk.END, log_entry['message'] + '\n', tuple(base_tags))
            else:
                last_index = 0
                sorted_links = sorted(links, key=lambda l: l[1])
                for link_type, link_start, link_end in sorted_links:
                    plain_text = log_entry['message'][last_index:link_start]
                    if plain_text:
                        self.log_area.insert(tk.END, plain_text, tuple(base_tags))
                    link_text = log_entry['message'][link_start:link_end]
                    link_tags = tuple(base_tags + [link_type])
                    self.log_area.insert(tk.END, link_text, link_tags)
                    last_index = link_end
                remaining_text = log_entry['message'][last_index:]
                if remaining_text:
                    self.log_area.insert(tk.END, remaining_text, tuple(base_tags))
                self.log_area.insert(tk.END, '\n')

            if scroll:
                self.log_area.see(tk.END)
            self.log_area.config(state='disabled')

        if to_file and self.is_running:
            if not hasattr(self, 'log_file') or not self.log_file or self.log_file.closed:
                try:
                    self.log_file = open(self.current_log_file_path, "a", encoding="utf-8", buffering=1)
                    self.log_file_open = True
                except IOError as e:
                    self.update_status(f"Error opening log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                    self.log_file = None
                    return
            if self.log_file and not self.log_file.closed:
                try:
                    self.log_file.write(message + '\n')
                    self.log_file.flush()
                except IOError as e:
                    self.update_status(f"Error writing to log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                        
    def update_progress_display(self, message):
        """
        # Updates the progress bar/spinner display area.
        # 진행률 표시줄/스피너 표시 영역을 업데이트합니다.
        """
        self.progress_label.config(text=message)

    def send_comment(self, event=None):
        """
        # Sends a comment or processes a command from the comment entry box.
        # 댓글 입력 상자에서 댓글을 보내거나 명령을 처리합니다.
        """
        if self.comment_entry['state'] == 'disabled': return "break"
        comment_text = self.comment_entry.get(1.0, tk.END).strip()
        if not comment_text: return "break"
        if comment_text.startswith("/"):
            self._process_command(comment_text)
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{timestamp}] [COMMENT] {comment_text}"
            insert_pos = self.selected_log_abs_index + 1 if self.selected_log_abs_index is not None else len(self.all_logs)
            new_log = {'message': formatted_message, 'level': 'COMMENT', 'state': 'ADDED'}
            self.all_logs.insert(insert_pos, new_log)
            self._record_action('add', {'line_num': insert_pos, 'log_entry': new_log})
            self.selected_log_line_index = self.selected_log_abs_index = None
            self._perform_search_and_filter_logs(scroll_to_end=False)
            self.update_status("Comment added.", self.theme.LOG_LEVEL_COLORS['ADDED'])
        
        self.comment_entry.delete(1.0, tk.END)
        return "break"

    def _record_action(self, action_type, details):
        """
        # Records a user action for the undo/redo stack.
        # 실행 취소/다시 실행 스택에 대한 사용자 작업을 기록합니다.
        """
        self.undo_stack.append({'type': action_type, 'details': details})
        self.redo_stack.clear()
        self.update_ui_for_state()

    def _undo(self, count=1):
        """
        # Undoes the last user action(s).
        # 마지막 사용자 작업을 실행 취소합니다.
        """
        undone = False
        for _ in range(count):
            if self.undo_stack:
                action = self.undo_stack.pop()
                action_type, details = action['type'], action['details']
                line_num = details['line_num']
                status_message = ""
                if action_type == 'add':
                    if 0 <= line_num < len(self.all_logs):
                        self.all_logs.pop(line_num)
                        self.redo_stack.append(action)
                        status_message = f"Undid: Add log at line {line_num + 1}"
                elif action_type == 'delete':
                    self.all_logs[line_num]['state'] = details['log_entry']['state']
                    self.all_logs[line_num]['message'] = details['log_entry']['message']
                    self.redo_stack.append(action)
                    status_message = f"Undid: Delete log at line {line_num + 1}"
                elif action_type == 'edit':
                    original_log = details['original_log']
                    current_log_state = copy.deepcopy(self.all_logs[line_num])
                    self.all_logs[line_num] = original_log
                    self.redo_stack.append({'type': 'edit', 'details': {'line_num': line_num, 'original_log': current_log_state}})
                    status_message = f"Undid: Edit log at line {line_num + 1}"
                
                self._perform_search_and_filter_logs(scroll_to_end=False)
                self.update_ui_for_state()
                if status_message: self.update_status(status_message, self.theme.LOG_LEVEL_COLORS['MODIFIED'])
                undone = True
            else: self.update_status("Nothing to undo.", self.theme.DISABLED_TEXT_COLOR); break
        if not undone: self.update_ui_for_state()

    def _redo(self, count=1):
        """
        # Redoes the last undone user action(s).
        # 마지막으로 실행 취소된 사용자 작업을 다시 실행합니다.
        """
        redone = False
        for _ in range(count):
            if self.redo_stack:
                action = self.redo_stack.pop()
                action_type, details = action['type'], action['details']
                line_num = details['line_num']
                status_message = ""
                if action_type == 'add':
                    self.all_logs.insert(line_num, details['log_entry'])
                    self.undo_stack.append(action)
                    status_message = f"Redid: Add log at line {line_num + 1}"
                elif action_type == 'delete':
                    if 0 <= line_num < len(self.all_logs):
                        self.all_logs[line_num]['state'] = 'DELETED'
                        self.all_logs[line_num]['message'] = 'DELETED: ' + details['log_entry']['message'].replace('DELETED: ', '', 1)
                        self.undo_stack.append(action)
                        status_message = f"Redid: Delete log at line {line_num + 1}"
                elif action_type == 'edit':
                    edited_log = details['original_log']
                    current_log_state = copy.deepcopy(self.all_logs[line_num])
                    self.all_logs[line_num] = edited_log
                    self.undo_stack.append({'type': 'edit', 'details': {'line_num': line_num, 'original_log': current_log_state}})
                    status_message = f"Redid: Edit log at line {line_num + 1}"

                self._perform_search_and_filter_logs(scroll_to_end=False)
                self.update_ui_for_state()
                if status_message: self.update_status(status_message, self.theme.LOG_LEVEL_COLORS['MODIFIED'])
                redone = True
            else: self.update_status("Nothing to redo.", self.theme.DISABLED_TEXT_COLOR); break
        if not redone: self.update_ui_for_state()

    def _show_command_dropdown(self):
        """
        # Shows a dropdown menu with available slash commands.
        # 사용 가능한 슬래시 명령어가 포함된 드롭다운 메뉴를 표시합니다.
        """
        if hasattr(self, 'command_popup') and self.command_popup.winfo_exists(): self.command_popup.destroy()
        if self.command_button['state'] == 'disabled': return
        self.command_popup = tk.Toplevel(self.master)
        self.command_popup.wm_overrideredirect(True)
        self.command_popup.config(bg=self.theme.WIDGET_BG_COLOR, bd=1, relief="solid")
        btn_x, btn_y, btn_height = self.command_button.winfo_rootx(), self.command_button.winfo_rooty(), self.command_button.winfo_height()
        commands = {
            "/add <TYPE> [content]": "Adds a new log of the specified TYPE.",
            "/delete": "Deletes the selected log line.",
            "/edit [content]": "Replaces the content of the selected log with [content].",
            "/undo [count]": "Undoes the last operation.", "/redo [count]": "Redoes the last undone operation."
        }
        self.command_listbox = tk.Listbox(self.command_popup, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, selectbackground=self.theme.ACCENT_COLOR, selectforeground=self.theme.BG_COLOR, highlightthickness=0, relief="flat")
        self.command_listbox.pack(fill="both", expand=True)
        self.command_listbox.bind("<<ListboxSelect>>", self._on_command_listbox_select)
        self.command_listbox.bind("<Motion>", self._on_command_listbox_motion)
        self.command_listbox.bind("<Leave>", self._on_command_listbox_leave)
        max_text = max([f"{cmd} | {desc}" for cmd, desc in commands.items()], key=len)
        temp_label = tk.Label(self.master, text=max_text, font=(self.theme.FONT_FAMILY_LOG, 10)); temp_label.update_idletasks()
        text_width = temp_label.winfo_reqwidth(); temp_label.destroy()
        popup_width = max(300, text_width + 40)
        for cmd, desc in commands.items(): self.command_listbox.insert(tk.END, f"{cmd} | {desc}")
        self.command_popup.wm_geometry(f"{popup_width}x{len(commands) * 20}+{btn_x}+{btn_y - (len(commands) * 20) - 5}")
        self.command_popup.attributes("-alpha", 0.0)
        self._animate_popup_fade_in(self.command_popup, 0.0, 1.0, 100, 10)
        self.command_popup.bind("<FocusOut>", lambda e: self.command_popup.destroy()); self.command_popup.focus_set()

    def _on_command_listbox_motion(self, event):
        """
        # Highlights a command in the dropdown on mouse hover.
        # 마우스 호버 시 드롭다운의 명령어를 하이라이트합니다.
        """
        index = self.command_listbox.nearest(event.y)
        if index != self.command_listbox.curselection():
            self.command_listbox.selection_clear(0, tk.END)
            self.command_listbox.selection_set(index)
            self.command_listbox.activate(index)

    def _on_command_listbox_leave(self, event):
        """
        # Clears the selection when the mouse leaves the command dropdown.
        # 마우스가 명령어 드롭다운을 벗어날 때 선택을 지웁니다.
        """
        self.command_listbox.selection_clear(0, tk.END)

    def _process_command(self, command_text):
        """
        # Parses and executes a slash command from the comment entry.
        # 댓글 입력창의 슬래시 명령어를 파싱하고 실행합니다.
        """
        parts = command_text.split(maxsplit=1)
        command = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""
        if command == "/delete":
            if self.selected_log_abs_index is not None and 0 <= self.selected_log_abs_index < len(self.all_logs):
                line_num = self.selected_log_abs_index
                original_log = copy.deepcopy(self.all_logs[line_num])
                self.all_logs[line_num]['state'] = 'DELETED'
                if not self.all_logs[line_num]['message'].strip().startswith('DELETED:'): self.all_logs[line_num]['message'] = 'DELETED: ' + original_log['message']
                self._record_action('delete', {'line_num': line_num, 'log_entry': original_log})
                self.update_status(f"Marked line {line_num + 1} for deletion.", self.theme.LOG_LEVEL_COLORS['DELETED'])
                self._perform_search_and_filter_logs(scroll_to_end=False)
                self.selected_log_line_index = self.selected_log_abs_index = None
            else: self.update_status("No log line selected for deletion.", self.theme.LOG_LEVEL_COLORS['DELETED'])
        elif command == "/edit":
            if self.selected_log_abs_index is not None and 0 <= self.selected_log_abs_index < len(self.all_logs) and args_str:
                line_num = self.selected_log_abs_index
                original_log = copy.deepcopy(self.all_logs[line_num])
                timestamp, current_level = datetime.now().strftime('%H:%M:%S'), self.all_logs[line_num].get('level', 'COMMENT')
                new_message = f"[{timestamp}] [{current_level}] {args_str}"
                self.all_logs[line_num]['message'], self.all_logs[line_num]['state'] = new_message, 'MODIFIED'
                self._record_action('edit', {'line_num': line_num, 'original_log': original_log})
                self.update_status(f"Edited line {line_num + 1}.", self.theme.LOG_LEVEL_COLORS['MODIFIED'])
                self._perform_search_and_filter_logs(scroll_to_end=False)
                self.selected_log_line_index = self.selected_log_abs_index = None
            else: self.update_status("No log line selected or no content provided for editing.", self.theme.LOG_LEVEL_COLORS['DELETED'])
        elif command == "/add":
            log_types = self.autocomplete_commands.get('/add', [])
            try:
                log_type_arg, content = args_str.split(maxsplit=1)
                log_type = log_type_arg.upper()
                if log_type in log_types and content:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    formatted_message = f"[{timestamp}] [{log_type}] {content}"
                    new_log = {'message': formatted_message, 'level': log_type, 'state': 'ADDED'}
                    insert_pos = self.selected_log_abs_index + 1 if self.selected_log_abs_index is not None else len(self.all_logs)
                    self.all_logs.insert(insert_pos, new_log)
                    self._record_action('add', {'line_num': insert_pos, 'log_entry': new_log})
                    self.update_status(f"Added {log_type} log at line {insert_pos + 1}.", self.theme.LOG_LEVEL_COLORS['ADDED'])
                    self._perform_search_and_filter_logs(scroll_to_end=False)
                    self.selected_log_line_index = self.selected_log_abs_index = None
                else: self.update_status(f"Usage: /add <TYPE> [content]. Valid types: {', '.join(log_types)}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            except ValueError: self.update_status("Usage: /add <TYPE> [content]. Invalid format.", self.theme.LOG_LEVEL_COLORS['DELETED'])
        elif command == "/undo": self._undo(int(args_str) if args_str.isdigit() else 1)
        elif command == "/redo": self._redo(int(args_str) if args_str.isdigit() else 1)
        else: self.update_status(f"Unknown command: {command}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        self.comment_entry.delete(1.0, tk.END)

    def _on_command_listbox_select(self, event):
        """
        # Handles selection from the command dropdown, inserting the command into the entry.
        # 명령어 드롭다운에서 선택을 처리하고, 명령어를 입력창에 삽입합니다.
        """
        if not self.command_listbox.curselection(): return
        selected_command_text = self.command_listbox.get(self.command_listbox.curselection()[0])
        base_command = selected_command_text.split(' | ')[0].split()[0]
        commands_that_need_space = ['/add', '/edit', '/undo', '/redo']
        final_text = base_command + (' ' if base_command in commands_that_need_space else '')
        self.comment_entry.delete(1.0, tk.END)
        self.comment_entry.insert(tk.END, final_text)
        self.command_popup.destroy()
        self.comment_entry.focus_set()
        self.comment_entry.mark_set(tk.INSERT, tk.END)
        self._handle_autocomplete(None)

    def _handle_autocomplete(self, event):
        """
        # Shows an autocomplete popup for command arguments (e.g., log levels for /add).
        # 명령어 인수에 대한 자동완성 팝업을 표시합니다 (예: /add에 대한 로그 레벨).
        """
        current_text = self.comment_entry.get("1.0", "end-1c")
        if self.autocomplete_popup and self.autocomplete_popup.winfo_exists(): self.autocomplete_popup.destroy(); self.autocomplete_popup = None
        parts = current_text.strip().split(' ', 1)
        command = parts[0]
        if command in self.autocomplete_commands and current_text.endswith(' ') and len(parts) == 1:
            arg_options = self.autocomplete_commands[command]
            self.autocomplete_popup = tk.Toplevel(self.master)
            self.autocomplete_popup.wm_overrideredirect(True)
            self.autocomplete_popup.config(bg=self.theme.WIDGET_BG_COLOR, bd=1, relief="solid")
            x, y, _, h = self.comment_entry.bbox("insert")
            root_x, root_y = self.comment_entry.winfo_rootx() + x, self.comment_entry.winfo_rooty() + y
            
            for option in arg_options:
                label = Label(self.autocomplete_popup, text=option, font=(self.theme.FONT_FAMILY_LOG, 9), bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, anchor="w", padx=5)
                label.pack(fill="x")
                label.bind("<Enter>", lambda e, l=label: l.config(bg=self.theme.ACCENT_COLOR, fg=self.theme.BG_COLOR))
                label.bind("<Leave>", lambda e, l=label: l.config(bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR))
                label.bind("<Button-1>", lambda e, o=option: self._on_autocomplete_select(o))

            popup_height = len(arg_options) * 22
            self.autocomplete_popup.geometry(f"100x{popup_height}+{root_x}+{root_y - popup_height - 2}")
            self.autocomplete_popup.bind("<FocusOut>", lambda e: self._close_autocomplete_popup())
            self.autocomplete_popup.focus_set()

    def _on_autocomplete_select(self, selected_arg):
        """
        # Inserts the selected autocomplete option into the comment entry.
        # 선택된 자동완성 옵션을 댓글 입력창에 삽입합니다.
        """
        base_command = self.comment_entry.get("1.0", "end-1c").strip().split(' ')[0]
        new_text = f"{base_command} {selected_arg} "
        self.comment_entry.delete("1.0", tk.END)
        self.comment_entry.insert("1.0", new_text)
        self.comment_entry.mark_set(tk.INSERT, tk.END)
        self.comment_entry.focus_set()
        self._close_autocomplete_popup()

    def update_status(self, message, color):
        """
        # Updates the status bar with a new message and color indicator.
        # 상태 표시줄을 새 메시지와 색상 표시기로 업데이트합니다.
        """
        self.status_label.config(text=message, fg=color)
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 8, 8, fill=color, outline=color)

    def toggle_run_exit(self):
        """
        # Toggles the execution of the target script (Run/Kill).
        # 대상 스크립트의 실행을 토글합니다 (실행/종료).
        """
        if self.is_running:
            if self.think_core_process and self.think_core_process.poll() is None:
                pid = self.think_core_process.pid
                try:
                    kill_command = f"taskkill /F /PID {pid} /T"
                    subprocess.run(kill_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.update_status(f"Killed process tree (PID: {pid}).", self.theme.LOG_LEVEL_COLORS['DELETED'])
                except Exception:
                    self.think_core_process.kill()
                    self.update_status(f"Killed process (PID: {pid}, fallback).", self.theme.LOG_LEVEL_COLORS['DELETED'])
        else:
            command_input = self.script_path_var.get().strip()
            if not command_input:
                self.update_status("Error: Script path is empty.", self.theme.LOG_LEVEL_COLORS['DELETED'])
                return

            command_to_run = []
            script_path = Path(command_input)
            
            if ' ' in command_input and not script_path.exists():
                command_to_run = shlex.split(command_input)
            else:
                if not script_path.is_file():
                    self.update_status(f"Error: Script not found at {command_input}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                    return

                ext = script_path.suffix.lower()
                interpreter_config = INTERPRETER_MAP.get(ext)

                if ext == '.py':
                    # Special handling for Python to check for 'python3' or 'python'
                    # 'python3' 또는 'python'을 확인하기 위한 Python 특별 처리
                    interpreter_path = shutil.which("python3") or shutil.which("python")
                    if interpreter_path:
                        command_to_run = [interpreter_path, str(script_path)]
                        self.update_status(f"Found interpreter '{os.path.basename(interpreter_path)}' for '.py' file.", self.theme.ACCENT_COLOR)
                    else:
                        self.update_status("Error: 'python' or 'python3' not found in PATH.", self.theme.LOG_LEVEL_COLORS['DELETED'])
                        return
                elif interpreter_config:
                    # Standard handling for other interpreters like 'go run', 'java -jar'
                    # 'go run', 'java -jar'와 같은 다른 인터프리터를 위한 표준 처리
                    base_command = interpreter_config[0]
                    interpreter_path = shutil.which(base_command)
                    if interpreter_path:
                        command_args = interpreter_config[1:]
                        command_to_run = [interpreter_path] + command_args + [str(script_path)]
                        self.update_status(f"Found interpreter '{base_command}' for '{ext}' file.", self.theme.ACCENT_COLOR)
                    else:
                        self.update_status(f"Error: Interpreter '{base_command}' not found in PATH.", self.theme.LOG_LEVEL_COLORS['DELETED'])
                        return
                elif os.access(script_path, os.X_OK):
                    # Fallback for executable files with no mapped interpreter
                    # 매핑된 인터프리터가 없는 실행 파일에 대한 폴백
                    command_to_run = [str(script_path)]
                    self.update_status("No interpreter mapped. Attempting to run file directly.", self.theme.LOG_LEVEL_COLORS['WARNING'])
                else:
                    # Error if no interpreter is found and the file is not executable
                    # 인터프리터를 찾을 수 없고 파일이 실행 가능하지 않은 경우 오류
                    self.update_status("Error: Unknown file type and no execute permission.", self.theme.LOG_LEVEL_COLORS['DELETED'])
                    return

            log_dir = self.log_dir_var.get()
            
            try:
                current_file_path = Path(__file__).resolve()
                target_path = Path(command_input.strip()).resolve()
                if current_file_path == target_path:
                    messagebox.showerror("Execution Error", "The Log Viewer cannot run its own source file. Please select the script you wish to monitor.")
                    return
            except (OSError, ValueError): pass
            
            if not Path(log_dir).is_dir():
                try: os.makedirs(log_dir, exist_ok=True)
                except OSError as e:
                    self.update_status(f"Error: Cannot create log directory: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                    return
            try: 
                if os.path.exists(PAUSE_FLAG_PATH): os.remove(PAUSE_FLAG_PATH)
            except Exception: pass

            self.is_paused = False
            self.all_logs.clear(); self.undo_stack.clear(); self.redo_stack.clear()
            self.log_area.config(state='normal'); self.log_area.delete(1.0, tk.END); self.log_area.config(state='disabled')
            self.update_status(f"Starting script: {Path(command_input).name}", self.theme.ACCENT_COLOR)
            self.master.update_idletasks()
            self.last_progress_message = None
            self.update_progress_display("")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"log_viewer_{timestamp}.log"

            self.current_log_file_path = os.path.join(log_dir, log_filename)
            self.log_file = None
            self.log_file_open = False

            try:
                if "--data-dir" not in command_to_run:
                    command_to_run.extend(["--data-dir", str(DATA_DIR)])

                project_root = Path(command_input.strip()).resolve().parent
                self.think_core_process = subprocess.Popen(
                    command_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding='utf-8', errors='replace', bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                    cwd=str(project_root)
                )
                self.is_running = True
                self.log_queue.put(('add', {'message': "Process started.", 'level': 'SYSTEM'}))
                threading.Thread(target=self._read_think_core_output, daemon=True).start()
                self.master.after(50, self.process_log_queue)
            except Exception as e: self.update_status(f"Error starting process: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        self.update_ui_for_state()

    def process_log_queue(self):
        """
        # Processes log messages from the queue and adds them to the display.
        # 큐의 로그 메시지를 처리하고 디스플레이에 추가합니다.
        """
        messages_processed = False
        try:
            while True:
                action, data = self.log_queue.get_nowait()
                messages_processed = True
                msg_text = data.get('message', '')
                all_log_types = "|".join(re.escape(k) for k in self.theme.LOG_LEVEL_COLORS.keys())
                log_level_pattern = rf"\s*\[({all_log_types})]\\/\[({all_log_types})?\]"
                level_match = re.search(log_level_pattern, msg_text, re.I)
                level = level_match.group(1).upper() if level_match else 'INFO'
                if level == 'PROGRESS':
                    self.update_progress_display(msg_text.replace('\r', '').strip())
                    self.last_progress_message = data
                    continue
                if self.last_progress_message:
                    is_resume_or_pause_message = bool(re.search(r'\b(resumed|paused)\b', msg_text, re.I))
                    if not self.is_paused and not is_resume_or_pause_message:
                        final_message = self.last_progress_message['message'].replace('\r', '').strip()
                        self.add_log(final_message, 'INFO', scroll=False)
                        self.last_progress_message = None
                        self.update_progress_display("")
                self.add_log(msg_text, level, scroll=False)
        except queue.Empty: pass
        finally:
            if messages_processed and self.log_area: self.log_area.see(tk.END)
            if self.is_running or not self.log_queue.empty(): self.master.after(50, self.process_log_queue)

    def _on_run_finish(self):
        """
        # Cleans up and updates the UI after the script process has finished.
        # 스크립트 프로세스가 완료된 후 UI를 정리하고 업데이트합니다.
        """
        self.is_running = False
        self.last_progress_message = None
        self.update_progress_display("")
        if hasattr(self, 'log_file') and self.log_file and not self.log_file.closed:
            self.log_file.close()
            self.log_file_open = True
        self.undo_stack.clear(); self.redo_stack.clear()
        self.update_ui_for_state()
        self._perform_search_and_filter_logs(scroll_to_end=False)
        self.update_status("Process finished.", self.theme.ACCENT_COLOR)

    def _read_think_core_output(self):
        """
        # Reads the output from the running script process in a separate thread.
        # 별도의 스레드에서 실행 중인 스크립트 프로세스의 출력을 읽습니다.
        """
        def enqueue_output(stream):
            for line in iter(stream.readline, ''):
                line_stripped = line.strip()
                if not line_stripped: continue
                self.log_queue.put(('add', {'message': line_stripped}))
            stream.close()
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.think_core_process.stdout,), daemon=True)
        stderr_thread = threading.Thread(target=enqueue_output, args=(self.think_core_process.stderr,), daemon=True)
        stdout_thread.start(); stderr_thread.start()
        self.think_core_process.wait()
        self.master.after(0, self._on_run_finish)

    def toggle_pause_resume(self):
        """
        # Toggles the paused/resumed state of the running script.
        # 실행 중인 스크립트의 일시정지/재개 상태를 토글합니다.
        """
        if self.is_paused:
            if self.undo_stack: self.save_log_changes()
            if os.path.exists(PAUSE_FLAG_PATH): os.remove(PAUSE_FLAG_PATH)
            self.is_paused = False
            self.log_queue.put(('add', {'message': f"[{datetime.now().strftime('%H:%M:%S')}] [SYSTEM] Process resumed.", 'level': 'SYSTEM'}))
        else:
            if not self.is_running: return
            with open(PAUSE_FLAG_PATH, "w") as f: f.write("paused")
            self.is_paused = True
            self._perform_search_and_filter_logs(scroll_to_end=False)
            self.log_queue.put(('add', {'message': f"[{datetime.now().strftime('%H:%M:%S')}] [SYSTEM] Process paused.", 'level': 'SYSTEM'}))
        self.update_ui_for_state()

    def open_log_folder(self):
        """
        # Opens the currently configured log directory in the file explorer.
        # 현재 설정된 로그 디렉토리를 파일 탐색기에서 엽니다.
        """
        log_dir = self.log_dir_var.get()
        if not Path(log_dir).is_dir():
            self.update_status(f"Log directory not found: {log_dir}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return
        try: 
            os.startfile(log_dir)
            self.update_status(f"Opened log folder: {log_dir}", self.theme.ACCENT_COLOR)
        except Exception as e: 
            self.update_status(f"Error opening folder: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])

    def _load_log_file(self, file_path: str):
        """
        # Loads and displays the content of a selected log file.
        # 선택된 로그 파일의 내용을 로드하고 표시합니다.
        """
        if not file_path or not os.path.isfile(file_path):
            self.update_status(f"Error: Log file not found at {file_path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return
        try:
            self.all_logs, self.undo_stack, self.redo_stack = [], [], []
            all_log_types = "|".join(re.escape(k) for k in self.theme.LOG_LEVEL_COLORS.keys())
            log_pattern = re.compile(rf"\s*\[({all_log_types})]\\/\[({all_log_types})?\]", re.I)
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            processed_lines = []
            for i, line in enumerate(lines):
                is_progress = "[PROGRESS]" in line
                if is_progress:
                    is_last_line = (i == len(lines) - 1)
                    next_line_is_not_progress = not is_last_line and "[PROGRESS]" not in lines[i + 1]
                    if is_last_line or next_line_is_not_progress:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            for line in processed_lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                match = log_pattern.search(line_stripped)
                level = match.group(1).upper() if match else "INFO"
                if level == 'PROGRESS':
                    level = 'INFO'
                self.all_logs.append({'message': line_stripped, 'level': level, 'state': 'SAVED'})
            self.log_file_open, self.is_running = True, False
            self.current_log_file_path = file_path
            self.log_dir_var.set(os.path.dirname(file_path))
            self._perform_search_and_filter_logs(scroll_to_end=True)
            self.update_status(f"Opened log file: {os.path.basename(file_path)}", self.theme.ACCENT_COLOR)
        except Exception as e: 
            self.update_status(f"Error reading log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        finally:
            self.update_ui_for_state()

    def open_log_file(self):
        """
        # Opens a file dialog to select and load a log file.
        # 로그 파일을 선택하고 로드하기 위한 파일 대화상자를 엽니다.
        """
        log_dir = self.log_dir_var.get()
        if not os.path.isdir(log_dir):
            self.update_status(f"Error: Log directory not found: {log_dir}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return
        file_path = filedialog.askopenfilename(initialdir=log_dir, title="Select Log File",
                                               filetypes=(("Log files", "*.log"), ("all files", "*.*")))
        if file_path:
            self._load_log_file(file_path)

    def _increase_font_size(self):
        """
        # Increases the font size of the log area.
        # 로그 영역의 글꼴 크기를 늘립니다.
        """
        self.log_font_size += 1; self.configure_tags(); self._perform_search_and_filter_logs(scroll_to_end=False)
        self.update_status(f"Font size: {self.log_font_size}", self.theme.ACCENT_COLOR)

    def _decrease_font_size(self):
        """
        # Decreases the font size of the log area.
        # 로그 영역의 글꼴 크기를 줄입니다.
        """
        if self.log_font_size > 8: 
            self.log_font_size -= 1
            self.configure_tags()
            self._perform_search_and_filter_logs(scroll_to_end=False)
            self.update_status(f"Font size: {self.log_font_size}", self.theme.ACCENT_COLOR)
        else: 
            self.update_status("Minimum font size reached.", self.theme.DISABLED_TEXT_COLOR)

    def exit_log_view_mode(self):
        """
        # Exits the log view mode and returns to the idle state.
        # 로그 보기 모드를 종료하고 유휴 상태로 돌아갑니다.
        """
        if self.editor_window_instance and self.editor_window_instance.winfo_exists(): self.editor_window_instance.close_window()
        self.log_file_open = False
        self.all_logs, self.undo_stack, self.redo_stack = [], [], []
        self.log_area.config(state='normal'); self.log_area.delete(1.0, tk.END); self.log_area.config(state='disabled')
        self.current_log_file_path = None
        self.update_ui_for_state()

    def save_log_changes(self):
        """
        # Saves any modifications (add, edit, delete) to the currently open log file.
        # 현재 열려있는 로그 파일에 대한 모든 수정 사항(추가, 편집, 삭제)을 저장합니다.
        """
        if not self.current_log_file_path:
            self.update_status("No log file open to save changes.", self.theme.LOG_LEVEL_COLORS['DELETED']); return
        logs_to_write = [{'state': 'SAVED', 'message': e['message'].replace('DELETED: ', '', 1), 'level': e['level']} for e in self.all_logs if e.get('state') != 'DELETED']
        self.all_logs = logs_to_write
        try:
            with open(self.current_log_file_path, 'w', encoding='utf-8') as f: 
                for log_entry in self.all_logs: f.write(log_entry['message'] + '\n')
            self.update_status(f"Changes saved to {os.path.basename(self.current_log_file_path)}", self.theme.LOG_LEVEL_COLORS['ADDED'])
            self.undo_stack, self.redo_stack = [], []
            self.selected_log_line_index = self.selected_log_abs_index = None
            self._perform_search_and_filter_logs(scroll_to_end=False)
        except Exception as e: self.update_status(f"Error saving changes: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        finally: self.update_ui_for_state()

    def update_ui_for_state(self):
        """
        # Updates the entire UI based on the current application state (Idle, Running, Paused, etc.).
        # 현재 애플리케이션 상태(유휴, 실행 중, 일시정지 등)에 따라 전체 UI를 업데이트합니다.
        """
        def style_btn(btn, text=None, bg=None, hover_color=None, state=None, command=None, **kwargs):
            style_kwargs = {
                'text': text, 'bg': bg, 'hover_color': hover_color,
                'state': state, 'command': command,
                'border_color': kwargs.get('border_color', self.theme.BUTTON_BORDER_COLOR),
                'hover_border_color': kwargs.get('hover_border_color', self.theme.ACCENT_COLOR),
                'fg': kwargs.get('fg', self.theme.BUTTON_STYLE['fg'])
            }
            btn.update_style(**{k: v for k, v in style_kwargs.items() if v is not None})

        current_state = "IDLE"
        if self.is_running:
            current_state = "PAUSED" if self.is_paused else "RUNNING"
        elif self.log_file_open:
            current_state = "LOG_VIEW"

        is_editable = current_state in ["PAUSED", "LOG_VIEW"]
        self.comment_entry.config(state="normal" if is_editable else "disabled")
        self.send_button.config(state="normal" if is_editable else "disabled")
        self.command_button.config(state="normal" if is_editable else "disabled")

        if current_state == "RUNNING":
            style_btn(self.run_exit_button, text="Kill", bg=self.theme.KILL_COLOR, hover_color=self.theme.KILL_HOVER_COLOR, state="normal", command=self.toggle_run_exit, hover_border_color=self.theme.KILL_HOVER_COLOR)
            style_btn(self.pause_resume_button, text="Pause", bg=self.theme.WARNING_COLOR, hover_color=self.theme.WARNING_HOVER_COLOR, state="normal", command=self.toggle_pause_resume, hover_border_color=self.theme.WARNING_HOVER_COLOR)
            self.update_status("Running...", self.theme.SUCCESS_COLOR)
            self.comment_entry.delete(1.0, tk.END); self.comment_entry.insert(tk.END, "Editing is only available in Paused or Stopped state."); self.comment_entry.config(fg=self.theme.DISABLED_TEXT_COLOR)

        elif current_state == "PAUSED":
            style_btn(self.run_exit_button, text="Kill", bg=self.theme.KILL_COLOR, hover_color=self.theme.KILL_HOVER_COLOR, state="normal", command=self.toggle_run_exit, hover_border_color=self.theme.KILL_HOVER_COLOR)
            if self.undo_stack:
                style_btn(self.pause_resume_button, text="Save & Resume", bg=self.theme.PRIMARY_COLOR, hover_color=self.theme.PRIMARY_HOVER_COLOR, state="normal", command=self.toggle_pause_resume)
            else:
                style_btn(self.pause_resume_button, text="Resume", bg=self.theme.SUCCESS_COLOR, hover_color=self.theme.SUCCESS_HOVER_COLOR, state="normal", command=self.toggle_pause_resume, hover_border_color=self.theme.SUCCESS_HOVER_COLOR)
            self.update_status("Paused. Editing enabled.", self.theme.ACCENT_COLOR)
            self.comment_entry.config(fg=self.theme.TEXT_COLOR); self.comment_entry.delete(1.0, tk.END)

        elif current_state == "LOG_VIEW":
            style_btn(self.run_exit_button, text="Exit", bg=self.theme.KILL_COLOR, hover_color=self.theme.KILL_HOVER_COLOR, state="normal", command=self.exit_log_view_mode, hover_border_color=self.theme.KILL_HOVER_COLOR)
            if self.undo_stack:
                style_btn(self.pause_resume_button, text="Save", bg=self.theme.PRIMARY_COLOR, hover_color=self.theme.PRIMARY_HOVER_COLOR, state="normal", command=self.save_log_changes)
            else:
                style_btn(self.pause_resume_button, text="Save", bg=self.theme.DISABLED_BUTTON_STYLE['bg'], fg=self.theme.DISABLED_TEXT_COLOR, state="disabled", command=lambda: None)
            if not self.undo_stack and "undo" not in self.status_label.cget("text").lower() and "redo" not in self.status_label.cget("text").lower():
                self.update_status(f"Viewing: {os.path.basename(self.current_log_file_path)}", self.theme.ACCENT_COLOR)
            self.comment_entry.config(fg=self.theme.TEXT_COLOR); self.comment_entry.delete(1.0, tk.END)

        else: # IDLE
            style_btn(self.run_exit_button, text="Run", bg=self.theme.SUCCESS_COLOR, hover_color=self.theme.SUCCESS_HOVER_COLOR, state="normal", command=self.toggle_run_exit, hover_border_color=self.theme.SUCCESS_HOVER_COLOR)
            style_btn(self.pause_resume_button, text="Pause", bg=self.theme.DISABLED_BUTTON_STYLE['bg'], fg=self.theme.DISABLED_TEXT_COLOR, state="disabled", command=lambda: None)
            self.update_status("Idle", self.theme.DISABLED_TEXT_COLOR)
            self.comment_entry.delete(1.0, tk.END); self.comment_entry.insert(tk.END, "Idle: Run or open a log file to start."); self.comment_entry.config(fg=self.theme.DISABLED_TEXT_COLOR)

if __name__ == "__main__":
    if DND_SUPPORT:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    initial_script_path = SCRIPT_PATH if Path(SCRIPT_PATH).is_file() else ""
    initial_log_dir = str(LOG_DIR)
    
    app = LogDisplay(master=root, script_path=initial_script_path, log_dir=initial_log_dir)
    app.mainloop()