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

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

from .theme import load_themes
from .config import PAUSE_FLAG_PATH, DATA_DIR
from .editor_window import EditorWindow
from .gui_widgets import StyledButton

class LogDisplay(tk.Frame):
    '''
    # 로그 뷰어의 메인 GUI 클래스입니다.
    # Main GUI class for the Log Viewer.
    '''
    def __init__(self, master=None, script_path: str = "", log_dir: str = ""):
        self.themes = load_themes()
        self.theme_name = tk.StringVar(value=list(self.themes.keys())[0])
        self.theme = self.themes[self.theme_name.get()]()
        
        self.custom_logs = self._load_custom_logs()
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
        
        self.script_path_var = tk.StringVar(value=script_path)
        self.log_dir_var = tk.StringVar(value=log_dir)

        self.all_logs = []; self.undo_stack = []; self.redo_stack = []
        self.log_filter_vars = {}
        self.filterable_log_types = [
            "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "COMMENT"
        ]
        self.filterable_log_types.extend(self.custom_logs.keys())

        for log_type in self.filterable_log_types:
            self.log_filter_vars[log_type] = BooleanVar(value=True)
        
        self.autocomplete_commands = {'/add': ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL"] + list(self.custom_logs.keys())}
        self.autocomplete_popup = None
        self.log_queue = queue.Queue()
        self.last_progress_message = None
        self.filter_button_text = tk.StringVar()
        self.filter_popup = None

        self.is_running = False; self.is_paused = False; self.log_file_open = False
        self.link_was_clicked = False; self.think_core_process = None; self.current_log_file_path = None
        self.log_area_insert_index = None; self.selected_log_line_index = None; self.selected_log_abs_index = None
        self.log_font_size = 10; self.editor_window_instance = None
        self._animation_ids = {}
        
        self.create_widgets()
        self.configure_tags()
        self.update_ui_for_state()
        self._setup_global_shortcuts()

    def _load_custom_logs(self):
        try:
            custom_log_file = Path(__file__).parent / "custom_logs.json"
            if custom_log_file.exists():
                with open(custom_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading custom_logs.json: {e}")
        return {}

    def _setup_global_shortcuts(self):
        self.master.bind_all("<Control-z>", lambda e: self._undo(1))
        self.master.bind_all("<Control-y>", lambda e: self._redo(1))
        self.master.bind_all("<Button-1>", self._on_global_click, add="+ ")

    def _animate_color(self, widget, start_color, end_color, duration=150, steps=15):
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
        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use('clam')
        style.configure("Custom.Vertical.TScrollbar", gripcount=0, background="#555555", darkcolor=self.theme.WIDGET_BG_COLOR, lightcolor=self.theme.WIDGET_BG_COLOR, troughcolor=self.theme.BG_COLOR, bordercolor=self.theme.BG_COLOR, relief="flat", arrowsize=0)
        style.map("Custom.Vertical.TScrollbar", background=[('active', self.theme.ACCENT_COLOR), ('!disabled', '#55555Gg')], relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        style.configure("Custom.TMenubutton",
            background=self.theme.WIDGET_BG_COLOR, foreground=self.theme.TEXT_COLOR,
            relief="flat", arrowcolor=self.theme.TEXT_COLOR, padding=5
        )
        style.map("Custom.TMenubutton",
            background=[('active', self.theme.HOVER_COLOR), ('!disabled', self.theme.WIDGET_BG_COLOR)],
            foreground=[('!disabled', self.theme.TEXT_COLOR)]
        )

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
        self.theme_menu = ttk.OptionMenu(self.config_frame, self.theme_name, self.theme_name.get(), *self.themes.keys(), command=self._on_theme_change, style="Custom.TMenubutton")
        self.theme_menu.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self._style_theme_popup_menu()

        filter_button_container = Frame(self.config_frame, bg=self.theme.BG_COLOR)
        filter_button_container.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5,0))
        self.filter_button = StyledButton(filter_button_container, self, textvariable=self.filter_button_text,
            font=(self.theme.FONT_FAMILY_UI, 10), padx=10, pady=5,
            bg=self.theme.FILTER_BUTTON_BG_COLOR, fg=self.theme.FILTER_BUTTON_FG_COLOR, hover_color=self.theme.FILTER_BUTTON_HOVER_BG_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.filter_button.pack(fill="x")
        self.filter_button.bind("<Button-1>", self._toggle_filter_dropdown)
        self._update_filter_button_text()
        
        top_frame = Frame(self, bg=self.theme.BG_COLOR)
        top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        button_frame = Frame(top_frame, bg=self.theme.BG_COLOR)
        button_frame.pack(side="left", fill="x", expand=True)
        
        btn_kwargs = {'font': self.theme.BUTTON_STYLE['font'], 'fg': self.theme.BUTTON_STYLE['fg'], 'padx': 15, 'pady': 5}
        self.run_exit_button = StyledButton(button_frame, self, text="Run", command=self.toggle_run_exit, **btn_kwargs,
            bg=self.theme.SUCCESS_COLOR, hover_color=self.theme.SUCCESS_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.SUCCESS_HOVER_COLOR)
        self.run_exit_button.pack(side="left", padx=5)
        
        self.pause_resume_button = StyledButton(button_frame, self, text="Pause", command=self.toggle_pause_resume, **btn_kwargs,
            bg=self.theme.WARNING_COLOR, hover_color=self.theme.WARNING_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.WARNING_HOVER_COLOR)
        self.pause_resume_button.pack(side="left", padx=5)

        self.open_log_folder_button = StyledButton(button_frame, self, text="Open Log Folder", command=self.open_log_folder, **btn_kwargs,
            bg=self.theme.PRIMARY_COLOR, hover_color=self.theme.PRIMARY_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.PRIMARY_HOVER_COLOR)
        self.open_log_folder_button.pack(side="left", padx=5)

        self.open_log_file_button = StyledButton(button_frame, self, text="Open Log File", command=self.open_log_file, **btn_kwargs,
            bg=self.theme.SECONDARY_COLOR, hover_color=self.theme.SECONDARY_HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.SECONDARY_HOVER_COLOR)
        self.open_log_file_button.pack(side="left", padx=5)

        font_control_frame = Frame(top_frame, bg=self.theme.BG_COLOR)
        font_control_frame.pack(side="right", padx=5)
        
        font_btn_kwargs = {'font': (self.theme.FONT_FAMILY_UI, 9), 'padx': 5, 'pady': 1}
        self.font_decrease_btn = StyledButton(font_control_frame, self, text="A-", command=self._decrease_font_size, **font_btn_kwargs,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.font_decrease_btn.pack(side="right")
        
        self.font_increase_btn = StyledButton(font_control_frame, self, text="A+", command=self._increase_font_size, **font_btn_kwargs,
            bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        self.font_increase_btn.pack(side="right", padx=(2,0))

        log_area_frame = Frame(self, bg=self.theme.BG_COLOR)
        log_area_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        text_sub_frame = Frame(log_area_frame, bg=self.theme.LOG_AREA_BG_COLOR)
        text_sub_frame.pack(side="top", fill="both", expand=True)
        text_sub_frame.grid_rowconfigure(0, weight=1)
        text_sub_frame.grid_columnconfigure(0, weight=1)

        self.log_area = tk.Text(text_sub_frame, wrap=tk.WORD, state='disabled', font=(self.theme.FONT_FAMILY_LOG, self.log_font_size), bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, bd=0, highlightthickness=0, padx=5, pady=5)
        self.log_area.grid(row=0, column=0, sticky="nsew")
        self.log_area.bind("<Button-1>", self._on_log_area_click)

        self.vsb = ttk.Scrollbar(text_sub_frame, orient="vertical", command=self.log_area.yview, style="Custom.Vertical.TScrollbar")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.log_area.config(yscrollcommand=self.vsb.set)
        
        self.progress_label = Label(log_area_frame, text="", font=(self.theme.FONT_FAMILY_LOG, self.log_font_size), bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.LOG_LEVEL_COLORS['PROGRESS'], anchor="w", padx=5)
        self.progress_label.pack(side="bottom", fill="x")

        bottom_frame = Frame(self, bg=self.theme.BG_COLOR)
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.comment_container_frame = Frame(bottom_frame, bg=self.theme.ENTRY_BG_COLOR)
        self.comment_container_frame.grid(row=0, column=0, sticky="ew")
        self.comment_container_frame.grid_columnconfigure(1, weight=1)

        self.command_button = tk.Button(self.comment_container_frame, text="/", command=self._show_command_dropdown, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 12), relief="flat", activebackground=self.theme.WIDGET_BG_COLOR, activeforeground=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR, bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.command_button.grid(row=0, column=0, sticky="nsew")
        
        self.comment_entry = tk.Text(self.comment_container_frame, font=(self.theme.FONT_FAMILY_UI, 11), bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, highlightthickness=0, height=1, wrap="none", padx=10, pady=8) # 비활성 배경색 추가        self.comment_entry.grid(row=0, column=1, sticky="ew")
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
        self.log_area.tag_bind("FILE_LINK", "<Control-Button-1>", self._on_link_click); self.log_area.tag_bind("FILE_LINK", "<Shift-Button-1>", self._on_link_shift_click)
        self.log_area.tag_bind("WEB_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("WEB_LINK", "<Leave>", self._on_link_leave)
        self.log_area.tag_bind("WEB_LINK", "<Control-Button-1>", self._on_link_click)
        
        overlay_bg = getattr(self.theme, 'DROP_OVERLAY_BG_COLOR', self.theme.HIGHLIGHT_BG_COLOR)
        overlay_fg = getattr(self.theme, 'DROP_OVERLAY_FG_COLOR', self.theme.TEXT_COLOR)
        self.dnd_overlay = Label(self.master, text="Drop File or Folder Here",
                         bg=overlay_bg, fg=overlay_fg, font=(self.theme.FONT_FAMILY_UI, 24, "bold"))

        self.update_ui_for_state()

    def on_entry_button_enter(self, button):
        if button['state'] == 'normal':
            self._animate_color(button, self.theme.ENTRY_BG_COLOR, self.theme.WIDGET_BG_COLOR)

    def on_entry_button_leave(self, button):
        if button['state'] == 'normal':
            self._animate_color(button, self.theme.WIDGET_BG_COLOR, self.theme.ENTRY_BG_COLOR)

    def _style_theme_popup_menu(self):
        try:
            popup_menu = self.theme_menu['menu']
            # 메뉴 팝업 자체의 테두리와 스타일 설정
            popup_menu.config(
                bg=self.theme.ACCENT_COLOR,  # 이 배경색이 테두리 색 역할을 함
                fg=self.theme.TEXT_COLOR,
                activebackground=self.theme.HOVER_COLOR,
                activeforeground=self.theme.TEXT_COLOR,
                relief='solid',
                bd=1,
                tearoff=0
            )

            end_index = popup_menu.index('end')
            if end_index is not None:
                for i in range(end_index + 1):
                    # 각 항목의 스타일을 다시 지정하여 내용 영역을 만듦
                    popup_menu.entryconfig(i,
                        background=self.theme.WIDGET_BG_COLOR,
                        foreground=self.theme.TEXT_COLOR,
                        activebackground=self.theme.HOVER_COLOR,
                        activeforeground=self.theme.TEXT_COLOR,
                        selectcolor=self.theme.ACCENT_COLOR
                    )
        except (tk.Toplevel, AttributeError):
            pass

    def _on_theme_change(self, theme_name: str):
        new_theme_class = self.themes.get(theme_name)
        if new_theme_class:
            self.theme = new_theme_class()
            self.theme.LOG_LEVEL_COLORS.update(self.custom_logs)
            self._apply_theme()
            # 에디터 창이 열려있으면 에디터의 테마도 업데이트
            if self.editor_window_instance and self.editor_window_instance.winfo_exists():
                self.editor_window_instance._apply_theme()

    def _apply_theme(self):
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
        style.configure("Custom.TMenubutton",
            background=self.theme.WIDGET_BG_COLOR, foreground=self.theme.TEXT_COLOR,
            arrowcolor=self.theme.TEXT_COLOR
        )
        # style.map을 아래와 같이 수정하여 foreground(글자색)를 명시적으로 다시 매핑합니다.
        style.map("Custom.TMenubutton",
            background=[('active', self.theme.HOVER_COLOR), ('!disabled', self.theme.WIDGET_BG_COLOR)],
            foreground=[('!disabled', self.theme.TEXT_COLOR)]
        )
        self._style_theme_popup_menu()

        if hasattr(self, 'dnd_overlay'):
            overlay_bg = getattr(self.theme, 'DROP_OVERLAY_BG_COLOR', self.theme.HIGHLIGHT_BG_COLOR)
            overlay_fg = getattr(self.theme, 'DROP_OVERLAY_FG_COLOR', self.theme.TEXT_COLOR)
            self.dnd_overlay.configure(bg=overlay_bg, fg=overlay_fg)
        
        self.config_frame.configure(bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR)
        self.script_entry.configure(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)
        self.log_dir_entry.configure(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR)
        
        btn_kwargs_theme = {'font': (self.theme.FONT_FAMILY_UI, 9), 
            'bg': self.theme.WIDGET_BG_COLOR, 'fg': self.theme.TEXT_COLOR, 'hover_color': self.theme.HOVER_COLOR,
            'border_color': self.theme.BUTTON_BORDER_COLOR, 'hover_border_color': self.theme.ACCENT_COLOR}
        self.script_browse_btn.update_style(**btn_kwargs_theme)
        self.log_dir_browse_btn.update_style(**btn_kwargs_theme)
        self.font_increase_btn.update_style(**btn_kwargs_theme)
        self.font_decrease_btn.update_style(**btn_kwargs_theme)
        self.filter_button.update_style(
            bg=self.theme.FILTER_BUTTON_BG_COLOR, fg=self.theme.FILTER_BUTTON_FG_COLOR, hover_color=self.theme.FILTER_BUTTON_HOVER_BG_COLOR,
            border_color=self.theme.BUTTON_BORDER_COLOR, hover_border_color=self.theme.ACCENT_COLOR)
        
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
        self.filter_logs()
        if self.editor_window_instance and self.editor_window_instance.winfo_exists():
            self.editor_window_instance.destroy()
            self.open_editor_window()

    def _is_restricted_folder(self, path: str) -> bool:
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
        self.dnd_overlay.place(in_=self.master, relx=0, rely=0, relwidth=1, relheight=1)
        self.dnd_overlay.lift()

    def _on_drag_leave(self, event):
        self.dnd_overlay.place_forget()

    def _on_drop(self, event):
        self.dnd_overlay.place_forget()
        try: paths = self.master.tk.splitlist(event.data)
        except (tk.TclError, AttributeError): paths = event.data.strip().replace("{", "").replace("}", "").split()
        if not paths: return
        path = paths[0] 
        if os.path.isfile(path):
            self.script_path_var.set(path)
            self.update_status(f"Script path set to: {os.path.basename(path)}", self.theme.LOG_LEVEL_COLORS['ADDED'])
        elif os.path.isdir(path):
            if self._is_restricted_folder(path):
                messagebox.showwarning("Restricted Folder", f"This folder is restricted and cannot be used as a log directory:\n\n{path}")
                self.update_status(f"Cannot use restricted folder: {path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            else:
                self.log_dir_var.set(path)
                self.update_status(f"Log directory set to: {os.path.basename(path)}", self.theme.LOG_LEVEL_COLORS['ADDED'])

    def _on_global_click(self, event):
        if not (hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists()): return
        widget_under_cursor = self.winfo_containing(event.x_root, event.y_root)
        if not widget_under_cursor:
            self._close_filter_dropdown()
            return
        w = widget_under_cursor
        while w:
            if w == self.filter_button or w == self.filter_popup: return
            try: w = w.master
            except Exception: break
        self._close_filter_dropdown()

    def _update_filter_button_text(self):
        enabled_count = sum(1 for var in self.log_filter_vars.values() if var.get())
        total_count = len(self.log_filter_vars)
        all_enabled = enabled_count == total_count
        is_open = hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists()
        arrow = "▲" if is_open else "▼"
        self.filter_button_text.set(f"Filters ({'All' if all_enabled else f'{enabled_count}/{total_count}'}) {arrow}")

    def _close_filter_dropdown(self, event=None):
        if hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists():
            self.filter_popup.destroy()
            self.filter_popup = None
        self._update_filter_button_text()

    def _toggle_filter_dropdown(self, event):
        if hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists():
            self._close_filter_dropdown()
            return
            
        self.filter_popup = popup = tk.Toplevel(self.master)
        popup.wm_overrideredirect(True)
        popup.wm_transient(self.master)
        popup.bind("<FocusOut>", self._close_filter_dropdown)

        self.master.update_idletasks()

        button_widget = event.widget if event else self.filter_button
        x = button_widget.winfo_rootx()

        DROPDOWN_BG_COLOR = getattr(self.theme, 'DROPDOWN_BG_COLOR', self.theme.WIDGET_BG_COLOR)
        DROPDOWN_BORDER_COLOR = getattr(self.theme, 'DROPDOWN_BORDER_COLOR', self.theme.ACCENT_COLOR)
        DROPDOWN_HOVER_BG_COLOR = getattr(self.theme, 'DROPDOWN_HOVER_BG_COLOR', self.theme.PRIMARY_HOVER_COLOR)

        main_frame = Frame(popup, bg=DROPDOWN_BG_COLOR, highlightbackground=DROPDOWN_BORDER_COLOR, highlightthickness=1)
        main_frame.pack()

        controls_frame = Frame(main_frame, bg=DROPDOWN_BG_COLOR)
        controls_frame.pack(fill='x', padx=10, pady=(10, 5))

        def select_all(select=True):
            for var in self.log_filter_vars.values(): var.set(select)
            self.filter_logs()

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
            chk = Checkbutton(container, text=log_type, variable=var, command=self.filter_logs,
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
        
        button_widget = event.widget if event else self.filter_button
        x = button_widget.winfo_rootx()
        y = button_widget.winfo_rooty() + button_widget.winfo_height() + 2
        
        popup_width = popup.winfo_width()
        popup_height = popup.winfo_height()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        if x + popup_width > screen_width: x = screen_width - popup_width
        if y + popup_height > screen_height: y = button_widget.winfo_rooty() - popup_height - 2
        if x < 0: x = 0
        if y < 0: y = 0

        popup.geometry(f"+{x}+{y}")
        popup.attributes("-alpha", 0)
        popup.deiconify()
        self._animate_popup_fade_in(popup, 0.0, 1.0, duration=100, steps=10)
        popup.focus_set()
        self._update_filter_button_text()

    def filter_logs(self, scroll_to_end=False):
        self._update_filter_button_text()
        current_scroll_fraction = self.log_area.yview()[0] 
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        for i, log_entry in enumerate(self.all_logs):
            level = log_entry.get('level', 'INFO')
            is_filterable = level in self.filterable_log_types
            should_display = not is_filterable or self.log_filter_vars.get(level, BooleanVar(value=True)).get()
            if log_entry.get('state') == 'DELETED' or should_display:
                tags = list(self._get_tags_for_log(log_entry)) + [f"log_index_{i}"]
                self.log_area.insert(tk.END, log_entry['message'] + '\n', tuple(tags))
                if len(log_entry['message']) > 0:
                    self._apply_link_tags(self.log_area.index(f"{tk.END}-2l"))
        self.log_area.configure(state='disabled')
        if scroll_to_end: self.log_area.yview_moveto(1.0)
        else: self.log_area.yview_moveto(current_scroll_fraction)

    def _browse_script_file(self):
        filepath = filedialog.askopenfilename(
            title="Select script to run",
            filetypes=(("Python files", "*.py"), ("All files", "*.*"))
        )
        if filepath:
            self.script_path_var.set(filepath)

    def _browse_log_dir(self):
        dirpath = filedialog.askdirectory(title="Select folder to save logs")
        if dirpath:
            self.log_dir_var.set(dirpath)
            
    def _on_link_enter(self, event):
        self.log_area.config(cursor="hand2")

    def _on_link_leave(self, event):
        self.log_area.config(cursor="")

    def _on_link_click(self, event):
        self.link_was_clicked = True
        index = self.log_area.index(f"@{event.x},{event.y}")
        tags = self.log_area.tag_names(index)
        link_type = "FILE_LINK" if "FILE_LINK" in tags else "WEB_LINK" if "WEB_LINK" in tags else None
        if link_type:
            tag_range = self.log_area.tag_prevrange(link_type, index)
            link_text = self.log_area.get(tag_range[0], tag_range[1]).strip('"')
            if link_type == "WEB_LINK":
                try: webbrowser.open_new_tab(link_text); self.update_status(f"Opened web page: {link_text}", self.theme.ACCENT_COLOR)
                except Exception as e: self.update_status(f"Error opening web page: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            elif link_type == "FILE_LINK":
                file_path = link_text.lstrip('@')
                try: os.startfile(os.path.normpath(file_path)); self.update_status(f"Opened file: {os.path.basename(file_path)}", self.theme.ACCENT_COLOR)
                except Exception as e: self.update_status(f"Error opening file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return "break"

    def _on_link_shift_click(self, event):
        self.link_was_clicked = True
        index = self.log_area.index(f"@{event.x},{event.y}")
        tags = self.log_area.tag_names(index)
        if "FILE_LINK" in tags:
            tag_range = self.log_area.tag_prevrange("FILE_LINK", index)
            link_text = self.log_area.get(tag_range[0], tag_range[1]).strip('"')
            file_path = link_text.lstrip('@')
            dir_path = os.path.dirname(os.path.normpath(file_path))
            if os.path.isdir(dir_path):
                try: os.startfile(dir_path); self.update_status(f"Opened folder: {dir_path}", self.theme.ACCENT_COLOR)
                except Exception as e: self.update_status(f"Error opening folder: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            else: self.update_status(f"Folder not found: {dir_path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return "break"
        
    def _on_comment_entry_focus_in(self, event):
        if self.comment_entry['state'] == 'disabled': return
        current_text = self.comment_entry.get(1.0, tk.END).strip()
        if current_text.startswith("Editing is only") or current_text.startswith("Idle:"): self.comment_entry.delete(1.0, tk.END)
        self.comment_entry.config(fg=self.theme.TEXT_COLOR)

    def _on_comment_entry_focus_out(self, event):
        new_focus = self.master.focus_get()
        if self.autocomplete_popup and self.autocomplete_popup.winfo_exists():
            if new_focus is not self.autocomplete_popup and new_focus not in self.autocomplete_popup.winfo_children(): self.autocomplete_popup.destroy(); self.autocomplete_popup = None
        if self.comment_entry['state'] == 'disabled' or not self.winfo_exists(): return
        if not self.comment_entry.get(1.0, tk.END).strip(): self.update_ui_for_state()
            
    def _on_comment_entry_key_press(self, event):
        if self.comment_entry['state'] == 'disabled': return "break"
        is_editable = not (self.is_running and not self.is_paused)
        if event.state & 0x4 and event.keysym.lower() == 'e' and is_editable: self.open_editor_window(); return "break"
        
    def open_editor_window(self):
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

    def _on_log_area_click(self, event):
        if self.link_was_clicked:
            self.link_was_clicked = False
            return

        is_editable = (self.is_running and self.is_paused) or not self.is_running
        if not is_editable:
            return "break"  # 편집 불가 상태일 때 모든 클릭 이벤트(선택 포함)를 막음

        # is_editable이 True일 때의 로직만 남김
        clicked_index = self.log_area.index(f"@{event.x},{event.y}")

        if is_editable:
            clicked_index = self.log_area.index(f"@{event.x},{event.y}")
            line_start = clicked_index.split('.')[0] + '.0'
            if self.selected_log_line_index == line_start or not self.log_area.get(line_start, f"{line_start} lineend").strip():
                self.selected_log_line_index = self.selected_log_abs_index = self.log_area_insert_index = None
                self._normalize_all_logs(scroll_to_end=False)
            else:
                tags = self.log_area.tag_names(line_start)
                abs_index = None
                for tag in tags:
                    if tag.startswith("log_index_"):
                        try: abs_index = int(tag.split('_')[-1]); break
                        except (ValueError, IndexError): continue
                if abs_index is None: return
                self._normalize_all_logs(scroll_to_end=False)
                self.log_area.tag_add("highlight", line_start, f"{line_start} lineend")
                self.log_area_insert_index = f"{line_start} lineend"
                self.selected_log_line_index = line_start
                self.selected_log_abs_index = abs_index
                self.update_status(f"Selected line {int(line_start.split('.')[0])}", self.theme.ACCENT_COLOR)
            if self.editor_window_instance and self.editor_window_instance.winfo_exists(): self.editor_window_instance.update_content(self.selected_log_abs_index)

    def _normalize_all_logs(self, scroll_to_end=True):
        self.filter_logs(scroll_to_end=scroll_to_end)

    def configure_tags(self):
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

    def _get_tags_for_log(self, log_entry):
        tags = [log_entry.get('level', 'INFO')]
        if 'state' in log_entry and log_entry['state'] != 'SAVED': tags.append(log_entry['state'])
        return tuple(tags)

    def _apply_link_tags(self, start_index, end_index=None):
        if end_index is None: end_index = f"{start_index.split('.')[0]}.end"
        line_text = self.log_area.get(start_index, end_index)
        if not line_text: return
        path_regex = r'([\'"]?)(@(?:[a-zA-Z]:(?:[\\/][^@\n\r<>"\'\\]*)?|(?:\.\.?[\\/])(?:[^@\n\r<>"\'\\]*)?))([\'"]?)'
        for match in re.finditer(path_regex, line_text):
            path_text = match.group(2)
            offset = match.group(0).find(path_text)
            tag_start = f"{start_index}+{match.start() + offset}c"
            tag_end = f"{tag_start}+{len(path_text)}c"
            self.log_area.tag_add("FILE_LINK", tag_start, tag_end)
        for match in re.finditer(r'https?://[^\s<>"\\]+', line_text):
            tag_start = f"{start_index}+{match.start()}c"
            tag_end = f"{start_index}+{match.end()}c"
            self.log_area.tag_add("WEB_LINK", tag_start, tag_end)

    def add_log(self, message, level='INFO', to_file=True, scroll=True):
        log_entry = {'message': message, 'level': level, 'state': 'SAVED'}
        self.all_logs.append(log_entry)
        is_filterable = level in self.filterable_log_types
        should_display = not is_filterable or self.log_filter_vars.get(level, BooleanVar(value=True)).get()
        if should_display:
            self.log_area.config(state='normal')
            tags = self._get_tags_for_log(log_entry)
            start_index = self.log_area.index(tk.END + "-1c")
            self.log_area.insert(tk.END, message + '\n', tags)
            self._apply_link_tags(start_index)
            if scroll: self.log_area.see(tk.END)
            self.log_area.config(state='disabled')
        if to_file and self.is_running and hasattr(self, 'log_file') and self.log_file and not self.log_file.closed:
            self.log_file.write(message + '\n')
            self.log_file.flush()

    def update_progress_display(self, message):
        self.progress_label.config(text=message)

    def send_comment(self, event=None):
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
            self.filter_logs(scroll_to_end=False)
            self.update_status("Comment added.", self.theme.LOG_LEVEL_COLORS['ADDED'])
        
        self.comment_entry.delete(1.0, tk.END)
        return "break"

    def _record_action(self, action_type, details):
        self.undo_stack.append({'type': action_type, 'details': details})
        self.redo_stack.clear()
        self.update_ui_for_state()

    def _undo(self, count=1):
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
                
                self.filter_logs(scroll_to_end=False)
                self.update_ui_for_state()
                if status_message: self.update_status(status_message, self.theme.LOG_LEVEL_COLORS['MODIFIED'])
                undone = True
            else: self.update_status("Nothing to undo.", self.theme.DISABLED_TEXT_COLOR); break
        if not undone: self.update_ui_for_state()

    def _redo(self, count=1):
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

                self.filter_logs(scroll_to_end=False)
                self.update_ui_for_state()
                if status_message: self.update_status(status_message, self.theme.LOG_LEVEL_COLORS['MODIFIED'])
                redone = True
            else: self.update_status("Nothing to redo.", self.theme.DISABLED_TEXT_COLOR); break
        if not redone: self.update_ui_for_state()

    def _show_command_dropdown(self):
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
        self.command_popup.wm_geometry(f"{popup_width}x{len(commands) * 20}+{btn_x}+{btn_y + btn_height + 5}")
        self.command_popup.attributes("-alpha", 0.0)
        self._animate_popup_fade_in(self.command_popup, 0.0, 1.0, 100, 10)
        self.command_popup.bind("<FocusOut>", lambda e: self.command_popup.destroy()); self.command_popup.focus_set()

    def _on_command_listbox_motion(self, event):
        index = self.command_listbox.nearest(event.y)
        if index != self.command_listbox.curselection():
            self.command_listbox.selection_clear(0, tk.END)
            self.command_listbox.selection_set(index)
            self.command_listbox.activate(index)

    def _on_command_listbox_leave(self, event):
        self.command_listbox.selection_clear(0, tk.END)

    def _process_command(self, command_text):
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
                self.filter_logs(scroll_to_end=False)
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
                self.filter_logs(scroll_to_end=False)
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
                    self.filter_logs(scroll_to_end=False)
                    self.selected_log_line_index = self.selected_log_abs_index = None
                else: self.update_status(f"Usage: /add <TYPE> [content]. Valid types: {', '.join(log_types)}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            except ValueError: self.update_status("Usage: /add <TYPE> [content]. Invalid format.", self.theme.LOG_LEVEL_COLORS['DELETED'])
        elif command == "/undo": self._undo(int(args_str) if args_str.isdigit() else 1)
        elif command == "/redo": self._redo(int(args_str) if args_str.isdigit() else 1)
        else: self.update_status(f"Unknown command: {command}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        self.comment_entry.delete(1.0, tk.END)

    def _on_command_listbox_select(self, event):
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
            self.autocomplete_popup.bind("<FocusOut>", lambda e: self.autocomplete_popup.destroy())
            self.autocomplete_popup.focus_set()

    def _on_autocomplete_select(self, selected_arg):
        base_command = self.comment_entry.get("1.0", "end-1c").strip().split(' ')[0]
        new_text = f"{base_command} {selected_arg} "
        self.comment_entry.delete("1.0", tk.END)
        self.comment_entry.insert("1.0", new_text)
        self.comment_entry.mark_set(tk.INSERT, tk.END)
        self.comment_entry.focus_set()
        if self.autocomplete_popup and self.autocomplete_popup.winfo_exists():
            self.autocomplete_popup.destroy()
            self.autocomplete_popup = None

    def update_status(self, message, color):
        self.status_label.config(text=message, fg=color)
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 8, 8, fill=color, outline=color)

    def toggle_run_exit(self):
        if self.is_running:
            if self.think_core_process and self.think_core_process.poll() is None: self.think_core_process.terminate()
        else:
            script_path = self.script_path_var.get()
            log_dir = self.log_dir_var.get()
            if not Path(script_path).is_file():
                self.update_status(f"Error: Script not found at {script_path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                return
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
            self.comment_entry.config(state='normal'); self.comment_entry.delete(1.0, tk.END)
            self.update_status(f"Starting script: {Path(script_path).name}", self.theme.ACCENT_COLOR)
            self.master.update_idletasks()
            self.last_progress_message = None
            self.update_progress_display("")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"glen_log_{timestamp}.log"
            self.current_log_file_path = os.path.join(log_dir, log_filename)
            try: self.log_file = open(self.current_log_file_path, "a", encoding="utf-8", buffering=1)
            except IOError as e: self.update_status(f"Error opening log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED']); return
            python_executable = sys.executable
            try:
                command_to_run = [python_executable, script_path, "--data-dir", DATA_DIR]
                project_root = Path(script_path).resolve().parent.parent.parent
                self.think_core_process = subprocess.Popen(
                    command_to_run, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding='utf-8', errors='replace', bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                    cwd=project_root
                )
                self.is_running = True
                self.log_file_open = True
                self.log_queue.put(('add', {'message': "Process started.", 'level': 'SYSTEM'}))
                threading.Thread(target=self._read_think_core_output, daemon=True).start()
                self.master.after(50, self.process_log_queue)
            except Exception as e: self.update_status(f"Error starting process: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        self.update_ui_for_state()

    def process_log_queue(self):
        messages_processed = False
        try:
            while True:
                action, data = self.log_queue.get_nowait()
                messages_processed = True
                msg_text = data.get('message', '')
                all_log_types = "|".join(re.escape(k) for k in self.theme.LOG_LEVEL_COLORS.keys())
                log_level_pattern = rf"\[({all_log_types})\]"
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
        self.is_running = False
        self.last_progress_message = None
        self.update_progress_display("")
        if hasattr(self, 'log_file') and self.log_file and not self.log_file.closed:
            self.log_file.close()
            self.log_file_open = True
        self.undo_stack.clear(); self.redo_stack.clear()
        self.update_ui_for_state()
        self.filter_logs(scroll_to_end=False)
        self.update_status("Process finished.", self.theme.ACCENT_COLOR)

    def _read_think_core_output(self):
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
        if self.is_paused:
            if self.undo_stack: self.save_log_changes()
            if os.path.exists(PAUSE_FLAG_PATH): os.remove(PAUSE_FLAG_PATH)
            self.is_paused = False
            self.log_queue.put(('add', {'message': f"[{datetime.now().strftime('%H:%M:%S')}] [SYSTEM] Process resumed.", 'level': 'SYSTEM'}))
        else:
            if not self.is_running: return
            with open(PAUSE_FLAG_PATH, "w") as f: f.write("paused")
            self.is_paused = True
            self.filter_logs(scroll_to_end=False)
            self.log_queue.put(('add', {'message': f"[{datetime.now().strftime('%H:%M:%S')}] [SYSTEM] Process paused.", 'level': 'SYSTEM'}))
        self.update_ui_for_state()

    def open_log_folder(self):
        log_dir = self.log_dir_var.get()
        if not Path(log_dir).is_dir():
            self.update_status(f"Log directory not found: {log_dir}", self.theme.LOG_LEVEL_COLORS['DELETED'])
            return
        try: 
            os.startfile(log_dir)
            self.update_status(f"Opened log folder: {log_dir}", self.theme.ACCENT_COLOR)
        except Exception as e: 
            self.update_status(f"Error opening folder: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])

    def open_log_file(self):
        log_dir = self.log_dir_var.get()
        if not os.path.isdir(log_dir):
            self.update_status(f"Error: Log directory not found: {log_dir}", self.theme.LOG_LEVEL_COLORS['DELETED']); return
        file_path = filedialog.askopenfilename(initialdir=log_dir, title="Select Log File", filetypes=(("Log files", "*.log"), ("all files", "*.*")))
        if not file_path: return
        try:
            self.all_logs, self.undo_stack, self.redo_stack = [], [], []
            all_log_types = "|".join(re.escape(k) for k in self.theme.LOG_LEVEL_COLORS.keys())
            log_pattern = re.compile(rf"\[({all_log_types})\]", re.I)
            with open(file_path, "r", encoding="utf-8") as f: lines = f.readlines()
            processed_lines = []
            for i, line in enumerate(lines):
                is_progress = "[PROGRESS]" in line
                if is_progress:
                    is_last_line = (i == len(lines) - 1)
                    next_line_is_not_progress = not is_last_line and "[PROGRESS]" not in lines[i+1]
                    if is_last_line or next_line_is_not_progress: processed_lines.append(line)
                else: processed_lines.append(line)
            for line in processed_lines:
                line_stripped = line.strip()
                if not line_stripped: continue
                match = log_pattern.search(line_stripped)
                level = match.group(1).upper() if match else "INFO"
                self.all_logs.append({'message': line_stripped, 'level': level, 'state': 'SAVED'})
            self.log_file_open, self.is_running = True, False
            self.current_log_file_path = file_path
            self.log_dir_var.set(os.path.dirname(file_path))
            self.filter_logs(scroll_to_end=True)
            self.update_status(f"Opened log file: {os.path.basename(file_path)}", self.theme.ACCENT_COLOR)
        except Exception as e:
            self.update_status(f"Error reading log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        self.update_ui_for_state()

    def _increase_font_size(self):
        self.log_font_size += 1; self.configure_tags(); self.filter_logs(scroll_to_end=False)
        self.update_status(f"Font size: {self.log_font_size}", self.theme.ACCENT_COLOR)

    def _decrease_font_size(self):
        if self.log_font_size > 8: 
            self.log_font_size -= 1
            self.configure_tags()
            self.filter_logs(scroll_to_end=False)
            self.update_status(f"Font size: {self.log_font_size}", self.theme.ACCENT_COLOR)
        else: 
            self.update_status("Minimum font size reached.", self.theme.DISABLED_TEXT_COLOR)

    def exit_log_view_mode(self):
        if self.editor_window_instance and self.editor_window_instance.winfo_exists(): self.editor_window_instance.close_window()
        self.log_file_open = False
        self.all_logs, self.undo_stack, self.redo_stack = [], [], []
        self.log_area.config(state='normal'); self.log_area.delete(1.0, tk.END); self.log_area.config(state='disabled')
        self.current_log_file_path = None
        self.update_ui_for_state()

    def save_log_changes(self):
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
            self.filter_logs(scroll_to_end=False)
        except Exception as e: self.update_status(f"Error saving changes: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        finally: self.update_ui_for_state()

    def update_ui_for_state(self):
        """
        앱 상태(Idle / Running / Paused / Log-View)에 따라
        버튼/입력창/상태라벨을 갱신
        """
        is_editable = (self.is_running and self.is_paused) or self.log_file_open

        # 입력/보내기/커맨드 활성화 여부
        if is_editable:
            self.comment_entry.config(state="normal", fg=self.theme.TEXT_COLOR)
            self.send_button.config(state="normal", fg=self.theme.ACCENT_COLOR)
            self.command_button.config(state="normal", fg=self.theme.ACCENT_COLOR)
        else:
            self.comment_entry.config(state="disabled", fg=self.theme.DISABLED_TEXT_COLOR)
            self.send_button.config(state="disabled", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR)
            self.command_button.config(state="disabled", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR)

        # Helper to update StyledButton appearance (bg + hover + borders)
        def style_btn(btn, text=None, bg=None, hover_color=None, border_color=None, hover_border_color=None, fg=None, state=None, command=None):
            kwargs = {}
            if text is not None: kwargs['text'] = text
            if bg is not None:
                kwargs['bg'] = bg
                # 하이라이트 색상을 배경색과 동일하게 설정하여 포커스 링 제거
                kwargs['highlightcolor'] = bg 
            if hover_color is not None: kwargs['hover_color'] = hover_color
            if border_color is not None: kwargs['border_color'] = border_color
            if hover_border_color is not None: kwargs['hover_border_color'] = hover_border_color
            if fg is not None: kwargs['fg'] = fg
            if state is not None: kwargs['state'] = state
            if command is not None: kwargs['command'] = command
            btn.update_style(**kwargs)

        # 상태별 버튼 구성
        if self.is_running:
            # Run → Kill (use update_style so StyledButton hover / bg state stays consistent)
            style_btn(
                self.run_exit_button,
                text="Kill",
                bg=self.theme.KILL_COLOR,
                hover_color=getattr(self.theme, 'KILL_HOVER_COLOR', self.theme.HOVER_COLOR),
                border_color=self.theme.BUTTON_BORDER_COLOR,
                hover_border_color=getattr(self.theme, 'KILL_HOVER_COLOR', self.theme.ACCENT_COLOR),
                state="normal",
                command=self.toggle_run_exit,
                fg=self.theme.BUTTON_STYLE['fg']
            )

            if self.is_paused:
                # Paused
                if getattr(self, "undo_stack", None):
                    style_btn(
                        self.pause_resume_button,
                        text="Save",
                        bg=self.theme.PRIMARY_COLOR,
                        hover_color=getattr(self.theme, 'PRIMARY_HOVER_COLOR', self.theme.HOVER_COLOR),
                        border_color=self.theme.BUTTON_BORDER_COLOR,
                        hover_border_color=self.theme.ACCENT_COLOR,
                        state="normal",
                        command=self.save_log_changes,
                        fg=self.theme.BUTTON_STYLE['fg']
                    )
                else:
                    style_btn(
                        self.pause_resume_button,
                        text="Resume",
                        bg=self.theme.SUCCESS_COLOR,
                        hover_color=getattr(self.theme, 'SUCCESS_HOVER_COLOR', self.theme.HOVER_COLOR),
                        border_color=self.theme.BUTTON_BORDER_COLOR,
                        hover_border_color=getattr(self.theme, 'SUCCESS_HOVER_COLOR', self.theme.ACCENT_COLOR),
                        state="normal",
                        command=self.toggle_pause_resume,
                        fg=self.theme.BUTTON_STYLE['fg']
                    )
                self.comment_entry.delete(1.0, tk.END)
                self.update_status("Paused. Editing enabled.", self.theme.ACCENT_COLOR)
            else:
                # Running
                style_btn(
                    self.pause_resume_button,
                    text="Pause",
                    bg=self.theme.WARNING_COLOR,
                    hover_color=getattr(self.theme, 'WARNING_HOVER_COLOR', self.theme.HOVER_COLOR),
                    border_color=self.theme.BUTTON_BORDER_COLOR,
                    hover_border_color=getattr(self.theme, 'WARNING_HOVER_COLOR', self.theme.ACCENT_COLOR),
                    state="normal",
                    command=self.toggle_pause_resume,
                    fg=self.theme.BUTTON_STYLE['fg']
                )
                self.comment_entry.delete(1.0, tk.END)
                self.comment_entry.insert(tk.END, "Editing is only available in Paused or Stopped state.")
                self.update_status("Running...", self.theme.SUCCESS_COLOR)

        elif self.log_file_open:
            # Log 파일 보기 모드: Run → Exit
            style_btn(
                self.run_exit_button,
                text="Exit",
                bg=self.theme.KILL_COLOR,
                hover_color=getattr(self.theme, 'KILL_HOVER_COLOR', self.theme.HOVER_COLOR),
                border_color=self.theme.BUTTON_BORDER_COLOR,
                hover_border_color=getattr(self.theme, 'KILL_HOVER_COLOR', self.theme.ACCENT_COLOR),
                state="normal",
                command=self.exit_log_view_mode,
                fg=self.theme.BUTTON_STYLE['fg']
            )

            style_btn(
                self.pause_resume_button,
                command=self.save_log_changes,
                text="Save",
                state="normal" if getattr(self, "undo_stack", None) else "disabled",
                bg=self.theme.PRIMARY_COLOR if getattr(self, "undo_stack", None) else self.theme.DISABLED_BUTTON_STYLE.get("bg", self.theme.WIDGET_BG_COLOR),
                hover_color=getattr(self.theme, 'PRIMARY_HOVER_COLOR', self.theme.HOVER_COLOR) if getattr(self, "undo_stack", None) else self.theme.HOVER_COLOR,
                fg=self.theme.BUTTON_STYLE['fg'] if getattr(self, "undo_stack", None) else self.theme.DISABLED_TEXT_COLOR
            )

            if not getattr(self, "undo_stack", None):
                # ensure the disabled look is fully applied
                self.pause_resume_button.update_style(state="disabled", bg=self.theme.DISABLED_BUTTON_STYLE.get("bg", self.theme.WIDGET_BG_COLOR), fg=self.theme.DISABLED_TEXT_COLOR)

            self.comment_entry.delete(1.0, tk.END)
            if (not self.undo_stack) and self.current_log_file_path and \
            "undo" not in self.status_label.cget("text").lower() and \
            "redo" not in self.status_label.cget("text").lower():
                self.update_status(f"Viewing: {os.path.basename(self.current_log_file_path)}", self.theme.ACCENT_COLOR)

        else:
            # Idle
            style_btn(
                self.run_exit_button,
                text="Run",
                bg=self.theme.SUCCESS_COLOR,
                hover_color=getattr(self.theme, 'SUCCESS_HOVER_COLOR', self.theme.HOVER_COLOR),
                border_color=self.theme.BUTTON_BORDER_COLOR,
                hover_border_color=getattr(self.theme, 'SUCCESS_HOVER_COLOR', self.theme.ACCENT_COLOR),
                state="normal",
                command=self.toggle_run_exit,
                fg=self.theme.BUTTON_STYLE['fg']
            )

            self.pause_resume_button.update_style(text="Disabled", state="disabled", bg=self.theme.DISABLED_BUTTON_STYLE.get("bg", self.theme.WIDGET_BG_COLOR), fg=self.theme.DISABLED_TEXT_COLOR)
            self.pause_resume_button.original_bg = self.theme.DISABLED_BUTTON_STYLE.get("bg")

            self.comment_entry.delete(1.0, tk.END)
            self.comment_entry.insert(tk.END, "Idle: Run or open a log file to start.")
            self.comment_entry.config(fg=self.theme.DISABLED_TEXT_COLOR) # 글자색 명시적 설정

            self.update_status("Idle", self.theme.DISABLED_TEXT_COLOR)
