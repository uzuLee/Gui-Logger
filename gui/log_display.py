# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\log_display.py

import tkinter as tk
from tkinter import Button, Checkbutton, Entry, Frame, BooleanVar, Label, filedialog, Canvas, Menu
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

from .theme import Theme
from .config import PAUSE_FLAG_PATH, DATA_DIR
from .editor_window import EditorWindow

class LogDisplay(tk.Frame):
    '''
    # 로그 뷰어의 메인 GUI 클래스입니다.
    # Main GUI class for the Log Viewer.
    '''
    def __init__(self, master=None, script_path: str = "", log_dir: str = ""):
        '''
        # LogDisplay 인스턴스를 초기화합니다.
        # Initializes the LogDisplay instance.

        # Args:
        #     master: 부모 위젯 (Parent widget)
        #     script_path (str): 실행할 스크립트의 초기 경로 (Initial path of the script to run)
        #     log_dir (str): 로그를 저장할 디렉토리의 초기 경로 (Initial path of the directory to save logs)
        '''
        self.theme = Theme()
        super().__init__(master, bg=self.theme.BG_COLOR)
        self.master = master
        self.master.title("Log Viewer")
        self.master.geometry("1200x850")
        self.master.configure(bg=self.theme.BG_COLOR)
        empty_menu = Menu(self.master); self.master.config(menu=empty_menu)
        self.pack(fill="both", expand=True)
        
        # 스크립트 경로와 로그 디렉토리 경로를 저장하는 Tkinter 변수
        # Tkinter variables to store the script path and log directory path
        self.script_path_var = tk.StringVar(value=script_path)
        self.log_dir_var = tk.StringVar(value=log_dir)

        # 로그 데이터 및 상태 관리 변수
        # Variables for managing log data and state
        self.all_logs = []; self.undo_stack = []; self.redo_stack = []
        self.log_filter_vars = {}
        self.filterable_log_types = [
            "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL",
            "THINKING", "DATA", "AUDIT", "SYSTEM", "COMMENT"
        ]
        for log_type in self.filterable_log_types:
            self.log_filter_vars[log_type] = BooleanVar(value=True)

        # 자동완성 및 UI 상태 변수
        # Variables for autocomplete and UI state
        self.autocomplete_commands = {'/add': ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "THINKING", "DATA", "AUDIT"]}
        self.autocomplete_popup = None
        self.log_queue = queue.Queue()
        self.last_progress_message = None
        self.filter_button_text = tk.StringVar()
        self.filter_popup = None

        # 실행 상태 및 플래그 변수
        # Variables for execution state and flags
        self.is_running = False; self.is_paused = False; self.log_file_open = False
        self.link_was_clicked = False; self.think_core_process = None; self.current_log_file_path = None
        self.log_area_insert_index = None; self.selected_log_line_index = None; self.selected_log_abs_index = None
        self.log_font_size = 10; self.editor_window_instance = None
        self._animation_ids = {}
        
        self.create_widgets()
        self.configure_tags()
        self.update_ui_for_state()
        self._setup_global_shortcuts()

    def _setup_global_shortcuts(self):
        '''
        # 애플리케이션 전역 단축키를 설정합니다 (예: Ctrl+Z, Ctrl+Y).
        # Sets up application-wide global shortcuts (e.g., Ctrl+Z, Ctrl+Y).
        '''
        self.master.bind_all("<Control-z>", lambda e: self._undo(1))
        self.master.bind_all("<Control-y>", lambda e: self._redo(1))
        self.master.bind_all("<Button-1>", self._on_global_click, add="+ ")

    def _animate_color(self, widget, start_color, end_color, duration=150, steps=15):
        '''
        # 위젯의 배경색을 부드럽게 전환하는 애니메이션을 적용합니다.
        # Animates the background color of a widget smoothly.
        '''
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
        '''
        # 팝업 창이 부드럽게 나타나는 페이드-인 애니메이션을 적용합니다.
        # Animates a popup window to fade in smoothly.
        '''
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
        '''
        # GUI의 모든 위젯을 생성하고 배치합니다.
        # Creates and places all widgets for the GUI.
        '''
        self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use('clam')
        style.configure("Custom.Vertical.TScrollbar", gripcount=0, background="#555555", darkcolor=self.theme.WIDGET_BG_COLOR, lightcolor=self.theme.WIDGET_BG_COLOR, troughcolor=self.theme.BG_COLOR, bordercolor=self.theme.BG_COLOR, relief="flat", arrowsize=0)
        style.map("Custom.Vertical.TScrollbar", background=[('active', self.theme.ACCENT_COLOR), ('!disabled', '#555555')], relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # --- 설정 프레임 (Configuration Frame) ---
        config_frame = tk.LabelFrame(self, text="Configuration", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10, "bold"), padx=10, pady=10)
        config_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        config_frame.grid_columnconfigure(1, weight=1)

        Label(config_frame, text="Script Path:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        script_entry = Entry(config_frame, textvariable=self.script_path_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, font=(self.theme.FONT_FAMILY_UI, 9))
        script_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        Button(config_frame, text="Browse...", command=self._browse_script_file, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat").grid(row=0, column=2, padx=5, pady=5)

        Label(config_frame, text="Log Directory:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        log_dir_entry = Entry(config_frame, textvariable=self.log_dir_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, font=(self.theme.FONT_FAMILY_UI, 9))
        log_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        Button(config_frame, text="Browse...", command=self._browse_log_dir, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat").grid(row=1, column=2, padx=5, pady=5)

        # --- 상단 제어 프레임 (Top Control Frame) ---
        top_frame = Frame(self, bg=self.theme.BG_COLOR)
        top_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        font_control_frame = Frame(top_frame, bg=self.theme.BG_COLOR)
        font_control_frame.pack(side="right", padx=5)
        Button(font_control_frame, text="A-", command=self._decrease_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5).pack(side="right")
        Button(font_control_frame, text="A+", command=self._increase_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5).pack(side="right", padx=(2,0))

        button_frame = Frame(top_frame, bg=self.theme.BG_COLOR)
        button_frame.pack(side="left", padx=(0, 10))
        
        def _bind_button_effects(button, default_bg, hover_bg):
            button.original_bg, button.hover_bg = default_bg, hover_bg
            def on_enter(event): 
                if button['state'] == 'normal': self._animate_color(button, button['bg'], button.hover_bg)
            def on_leave(event):
                if button['state'] == 'normal': self._animate_color(button, button['bg'], button.original_bg)
            button.bind("<Enter>", on_enter, add="+ "); button.bind("<Leave>", on_leave, add="+ ")

        self.run_exit_button = Button(button_frame, text="Run", command=self.toggle_run_exit, bg=self.theme.SUCCESS_COLOR, **self.theme.BUTTON_STYLE)
        self.run_exit_button.pack(side="left", padx=5)
        _bind_button_effects(self.run_exit_button, self.theme.SUCCESS_COLOR, self.theme.SUCCESS_HOVER_COLOR)
        
        self.pause_resume_button = Button(button_frame, text="Pause", command=self.toggle_pause_resume, bg=self.theme.WARNING_COLOR, **self.theme.BUTTON_STYLE)
        self.pause_resume_button.pack(side="left", padx=5)
        _bind_button_effects(self.pause_resume_button, self.theme.WARNING_COLOR, self.theme.WARNING_HOVER_COLOR)

        open_log_folder_button = Button(button_frame, text="Open Log Folder", command=self.open_log_folder, bg=self.theme.PRIMARY_COLOR, **self.theme.BUTTON_STYLE)
        open_log_folder_button.pack(side="left", padx=5)
        _bind_button_effects(open_log_folder_button, self.theme.PRIMARY_COLOR, self.theme.PRIMARY_HOVER_COLOR)

        open_log_file_button = Button(button_frame, text="Open Log File", command=self.open_log_file, bg=self.theme.SECONDARY_COLOR, **self.theme.BUTTON_STYLE)
        open_log_file_button.pack(side="left", padx=5)
        _bind_button_effects(open_log_file_button, self.theme.SECONDARY_COLOR, self.theme.SECONDARY_HOVER_COLOR)

        filter_button_container = Frame(top_frame, bg=self.theme.BG_COLOR)
        filter_button_container.pack(side="left", fill="x", expand=True)

        self.filter_button = Button(filter_button_container, textvariable=self.filter_button_text,
                                    bg=getattr(self.theme, 'FILTER_BUTTON_BG_COLOR', self.theme.WIDGET_BG_COLOR),
                                    fg=getattr(self.theme, 'FILTER_BUTTON_FG_COLOR', self.theme.TEXT_COLOR),
                                    activebackground=getattr(self.theme, 'FILTER_BUTTON_ACTIVE_BG_COLOR', self.theme.CLICK_COLOR),
                                    font=(self.theme.FONT_FAMILY_UI, 10), relief="flat",
                                    padx=10, pady=5)
        self.filter_button.pack(fill="x")
        self.filter_button.bind("<Button-1>", self._toggle_filter_dropdown)
        self._bind_button_effects(self.filter_button, 
                                getattr(self.theme, 'FILTER_BUTTON_BG_COLOR', self.theme.WIDGET_BG_COLOR), 
                                getattr(self.theme, 'FILTER_BUTTON_HOVER_BG_COLOR', self.theme.HOVER_COLOR))
        self._update_filter_button_text()
        
        # --- 로그 표시 영역 (Log Area) ---
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

        # --- 하단 입력 및 상태 프레임 (Bottom Input and Status Frame) ---
        bottom_frame = Frame(self, bg=self.theme.BG_COLOR)
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        comment_container_frame = Frame(bottom_frame, bg=self.theme.ENTRY_BG_COLOR)
        comment_container_frame.grid(row=0, column=0, sticky="ew")
        comment_container_frame.grid_columnconfigure(1, weight=1)
        self.command_button = Button(comment_container_frame, text="/", command=self._show_command_dropdown, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 12), relief="flat", activebackground=self.theme.ENTRY_BG_COLOR, activeforeground="white", bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.command_button.grid(row=0, column=0, sticky="nsew")
        self.command_button.bind("<Enter>", lambda e: self.command_button.config(fg=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR) if self.command_button['state'] == 'normal' else None)
        self.command_button.bind("<Leave>", lambda e: self.command_button.config(fg=self.theme.ACCENT_COLOR) if self.command_button['state'] == 'normal' else None)
        self.comment_entry = tk.Text(comment_container_frame, font=(self.theme.FONT_FAMILY_UI, 11), bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, relief="flat", bd=0, highlightthickness=0, height=1, wrap="none", padx=10, pady=8)
        self.comment_entry.grid(row=0, column=1, sticky="ew")
        self.comment_entry.bind("<Return>", self.send_comment); self.comment_entry.bind("<Shift-Return>", "break")
        self.comment_entry.bind("<FocusIn>", self._on_comment_entry_focus_in); self.comment_entry.bind("<FocusOut>", self._on_comment_entry_focus_out)
        self.comment_entry.bind("<Key>", self._on_comment_entry_key_press); self.comment_entry.bind("<KeyRelease>", self._handle_autocomplete)
        self.send_button = Button(comment_container_frame, text="➤", command=self.send_comment, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 14, "bold"), relief="flat", activebackground=self.theme.ENTRY_BG_COLOR, activeforeground="white", bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.send_button.grid(row=0, column=2, sticky="nsew")
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(fg=self.theme.COMMAND_BUTTON_HOVER_FG_COLOR))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(fg=self.theme.ACCENT_COLOR) if self.send_button['state'] == 'normal' else None)
        status_frame = Frame(bottom_frame, bg=self.theme.BG_COLOR); status_frame.grid(row=1, column=0, sticky="e", padx=5, pady=(5,0))
        self.status_canvas = Canvas(status_frame, width=10, height=10, bg=self.theme.BG_COLOR, highlightthickness=0); self.status_canvas.pack(side="left", pady=2)
        self.status_label = Label(status_frame, text="Idle", font=(self.theme.FONT_FAMILY_UI, 9), bg=self.theme.BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR); self.status_label.pack(side="left", padx=(5,0))
        self.log_area.tag_bind("FILE_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("FILE_LINK", "<Leave>", self._on_link_leave)
        self.log_area.tag_bind("FILE_LINK", "<Control-Button-1>", self._on_link_click); self.log_area.tag_bind("FILE_LINK", "<Shift-Button-1>", self._on_link_shift_click)
        self.log_area.tag_bind("WEB_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("WEB_LINK", "<Leave>", self._on_link_leave)
        self.log_area.tag_bind("WEB_LINK", "<Control-Button-1>", self._on_link_click)
        self.update_ui_for_state()

    def _on_global_click(self, event):
        '''
        # 전역 클릭 이벤트를 처리하여 필터 드롭다운 외부를 클릭했을 때 닫히도록 합니다.
        # Handles global click events to close the filter dropdown when clicking outside of it.
        '''
        if not (hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists()):
            return

        widget_under_cursor = self.winfo_containing(event.x_root, event.y_root)
        if not widget_under_cursor:
            self._close_filter_dropdown()
            return

        w = widget_under_cursor
        while w:
            if w == self.filter_button:
                return
            if w == self.filter_popup:
                return
            try:
                w = w.master
            except Exception:
                break
        
        self._close_filter_dropdown()

    def _update_filter_button_text(self):
        '''
        # 필터 버튼의 텍스트를 현재 필터 상태에 맞게 업데이트합니다.
        # Updates the filter button's text to reflect the current filter state.
        '''
        enabled_count = sum(1 for var in self.log_filter_vars.values() if var.get())
        total_count = len(self.log_filter_vars)
        all_enabled = enabled_count == total_count
        
        is_open = hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists()
        arrow = "▲" if is_open else "▼"
        
        self.filter_button_text.set(f"Filters ({'All' if all_enabled else f'{enabled_count}/{total_count}'}) {arrow}")

    def _close_filter_dropdown(self, event=None):
        '''
        # 필터 드롭다운 팝업을 닫습니다.
        # Closes the filter dropdown popup.
        '''
        if hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists():
            self.filter_popup.destroy()
            self.filter_popup = None
        self._update_filter_button_text()

    def _toggle_filter_dropdown(self, event):
        '''
        # 필터 드롭다운 메뉴를 열거나 닫습니다.
        # Toggles the filter dropdown menu open or closed.
        '''
        if hasattr(self, 'filter_popup') and self.filter_popup and self.filter_popup.winfo_exists():
            self._close_filter_dropdown()
            return
            
        self.filter_popup = popup = tk.Toplevel(self.master)
        popup.wm_overrideredirect(True)
        popup.wm_transient(self.master)
        
        # 팝업이 포커스를 잃으면 닫히도록 바인딩
        popup.bind("<FocusOut>", self._close_filter_dropdown)

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

        all_button = Button(controls_frame, text="Select All", command=lambda: select_all(True), bg=DROPDOWN_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", font=(self.theme.FONT_FAMILY_UI, 9), activebackground=DROPDOWN_HOVER_BG_COLOR)
        all_button.pack(side="left", padx=(5,0))
        self._bind_button_effects(all_button, DROPDOWN_BG_COLOR, DROPDOWN_HOVER_BG_COLOR)

        none_button = Button(controls_frame, text="Deselect All", command=lambda: select_all(False), bg=DROPDOWN_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", font=(self.theme.FONT_FAMILY_UI, 9), activebackground=DROPDOWN_HOVER_BG_COLOR)
        none_button.pack(side="left", padx=5)
        self._bind_button_effects(none_button, DROPDOWN_BG_COLOR, DROPDOWN_HOVER_BG_COLOR)
        
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
        
        popup.update_idletasks() # 팝업의 실제 크기를 계산

        button_widget = event.widget
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
        '''
        # 현재 필터 설정에 따라 로그를 필터링하여 다시 표시합니다.
        # Filters and redisplays the logs according to the current filter settings.
        '''
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
                self._apply_link_tags(self.log_area.index(f"{tk.END}-2l"))

        self.log_area.configure(state='disabled')
        if scroll_to_end: self.log_area.yview_moveto(1.0)
        else: self.log_area.yview_moveto(current_scroll_fraction)

    def _browse_script_file(self):
        '''
        # '파일 찾아보기' 대화상자를 열어 실행할 스크립트 파일을 선택합니다.
        # Opens a 'file browse' dialog to select a script file to run.
        '''
        filepath = filedialog.askopenfilename(
            title="Select script to run",
            filetypes=(("Python files", "*.py"), ("All files", "*.*"))
        )
        if filepath:
            self.script_path_var.set(filepath)

    def _browse_log_dir(self):
        '''
        # '폴더 찾아보기' 대화상자를 열어 로그를 저장할 디렉토리를 선택합니다.
        # Opens a 'folder browse' dialog to select a directory to save logs.
        '''
        dirpath = filedialog.askdirectory(title="Select folder to save logs")
        if dirpath:
            self.log_dir_var.set(dirpath)
            
    def _on_link_enter(self, event):
        '''
        # 링크 위로 마우스 커서가 올라가면 커서 모양을 변경합니다.
        # Changes the cursor shape when the mouse hovers over a link.
        '''
        self.log_area.config(cursor="hand2")

    def _on_link_leave(self, event):
        '''
        # 링크에서 마우스 커서가 벗어나면 커서 모양을 원래대로 되돌립니다.
        # Reverts the cursor shape when the mouse leaves a link.
        '''
        self.log_area.config(cursor="")

    def _on_link_click(self, event):
        '''
        # 파일 또는 웹 링크를 클릭했을 때의 동작을 처리합니다 (Ctrl+Click).
        # Handles the action when a file or web link is clicked (Ctrl+Click).
        '''
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
        '''
        # 파일 링크를 Shift+Click했을 때 파일이 있는 폴더를 엽니다.
        # Opens the folder containing the file when a file link is Shift+Clicked.
        '''
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
        '''
        # 코멘트 입력창에 포커스가 들어왔을 때 플레이스홀더 텍스트를 제거합니다.
        # Removes placeholder text when the comment entry gets focus.
        '''
        if self.comment_entry['state'] == 'disabled': return
        current_text = self.comment_entry.get(1.0, tk.END).strip()
        if current_text.startswith("Editing is only") or current_text.startswith("Idle:"): self.comment_entry.delete(1.0, tk.END)
        self.comment_entry.config(fg=self.theme.TEXT_COLOR)

    def _on_comment_entry_focus_out(self, event):
        '''
        # 코멘트 입력창에서 포커스가 나갔을 때, 내용이 없으면 플레이스홀더를 다시 표시합니다.
        # Restores placeholder text if the comment entry is empty when it loses focus.
        '''
        new_focus = self.master.focus_get()
        if self.autocomplete_popup and self.autocomplete_popup.winfo_exists():
            if new_focus is not self.autocomplete_popup and new_focus not in self.autocomplete_popup.winfo_children(): self.autocomplete_popup.destroy(); self.autocomplete_popup = None
        if self.comment_entry['state'] == 'disabled' or not self.winfo_exists(): return
        if not self.comment_entry.get(1.0, tk.END).strip(): self.update_ui_for_state()
            
    def _on_comment_entry_key_press(self, event):
        '''
        # 코멘트 입력창에서 키가 눌렸을 때의 동작을 처리합니다 (예: Ctrl+E로 에디터 열기).
        # Handles key presses in the comment entry (e.g., Ctrl+E to open editor).
        '''
        if self.comment_entry['state'] == 'disabled': return "break"
        is_editable = not (self.is_running and not self.is_paused)
        if event.state & 0x4 and event.keysym.lower() == 'e' and is_editable: self.open_editor_window(); return "break"
        
    def open_editor_window(self):
        '''
        # 로그 에디터 창을 열거나 이미 열려있으면 맨 앞으로 가져옵니다.
        # Opens the log editor window, or brings it to the front if already open.
        '''
        if self.editor_window_instance and self.editor_window_instance.winfo_exists(): self.editor_window_instance.lift(); self.editor_window_instance.focus_set(); return
        self.editor_window_instance = EditorWindow(self, self.selected_log_abs_index)

    def _on_log_area_click(self, event):
        '''
        # 로그 영역을 클릭했을 때의 동작을 처리하여 로그 라인을 선택/해제합니다.
        # Handles clicks in the log area to select/deselect log lines.
        '''
        if self.link_was_clicked: self.link_was_clicked = False; return

        is_editable = not self.is_running or self.is_paused
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
        '''
        # 모든 로그의 하이라이트를 제거하고 필터를 다시 적용합니다.
        # Removes highlights from all logs and reapplies filters.
        '''
        self.filter_logs(scroll_to_end=scroll_to_end)

    def configure_tags(self):
        '''
        # 로그 레벨, 하이라이트, 링크 등에 대한 텍스트 태그 스타일을 설정합니다.
        # Configures text tag styles for log levels, highlights, links, etc.
        '''
        base_font = (self.theme.FONT_FAMILY_LOG, self.log_font_size)
        self.log_area.config(font=base_font)
        
        for level, color in self.theme.LOG_LEVEL_COLORS.items():
            font_config = list(base_font)
            extra_config = {}
            if level == "FATAL": font_config.extend(["bold"])
            elif level in ["COMMENT", "ADDED", "MODIFIED", "SYSTEM", "AUDIT", "THINKING"]: font_config.extend(["italic"])
            elif level == "DELETED": extra_config["overstrike"] = True
            
            self.log_area.tag_config(level, foreground=color, font=tuple(font_config), **extra_config)
        
        self.log_area.tag_config("highlight", background=self.theme.HIGHLIGHT_BG_COLOR, foreground=self.theme.HIGHLIGHT_FG_COLOR)
        self.log_area.tag_config("FILE_LINK", foreground=self.theme.LINK_COLOR, underline=True)
        self.log_area.tag_config("WEB_LINK", foreground=self.theme.LINK_COLOR, underline=True)

    def _get_tags_for_log(self, log_entry):
        '''
        # 로그 항목에 적용할 태그 목록을 반환합니다.
        # Returns a list of tags to apply to a log entry.
        '''
        tags = [log_entry.get('level', 'INFO')]
        if 'state' in log_entry and log_entry['state'] != 'SAVED': tags.append(log_entry['state'])
        return tuple(tags)

    def _apply_link_tags(self, start_index, end_index=None):
        '''
        # 지정된 텍스트 범위 내에서 파일 및 웹 링크를 찾아 태그를 적용합니다.
        # Finds and applies tags to file and web links within a specified text range.
        '''
        if end_index is None: end_index = f"{start_index.split('.')[0]}.end"
        line_text = self.log_area.get(start_index, end_index)
        path_regex = r'([\"\"]?)(@(?:[a-zA-Z]:(?:[\\/][^@\n\r<>\"\']*)?|(?:\.\.?[\\/])(?:[^@\n\r<>\"\']*)?))([\"\"]?)'
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
        '''
        # 새 로그 항목을 내부 목록과 GUI에 추가합니다.
        # Adds a new log entry to the internal list and the GUI.
        '''
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
        '''
        # 진행률 표시 레이블의 텍스트를 업데이트합니다.
        # Updates the text of the progress display label.
        '''
        self.progress_label.config(text=message)

    def send_comment(self, event=None):
        '''
        # 코멘트 입력창의 내용을 로그에 추가합니다.
        # Adds the content of the comment entry to the log.
        '''
        if self.comment_entry['state'] == 'disabled': return "break"
        comment_text = self.comment_entry.get(1.0, tk.END).strip()
        if not comment_text: return "break"
        
        is_editable = not (self.is_running and not self.is_paused)
        if not is_editable: return "break"

        if comment_text.startswith("/"): self._process_command(comment_text)
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
        '''
        # 실행 취소(undo)를 위해 사용자 작업을 기록합니다.
        # Records a user action for undo purposes.
        '''
        self.undo_stack.append({'type': action_type, 'details': details})
        self.redo_stack.clear()
        self.update_ui_for_state()

    def _undo(self, count=1):
        '''
        # 마지막 작업을 실행 취소합니다.
        # Undoes the last action.
        '''
        pass

    def _redo(self, count=1):
        '''
        # 마지막으로 실행 취소한 작업을 다시 실행합니다.
        # Redoes the last undone action.
        '''
        pass

    def _show_command_dropdown(self):
        '''
        # 사용 가능한 슬래시(/) 명령 목록을 보여주는 드롭다운을 표시합니다.
        # Shows a dropdown with a list of available slash (/) commands.
        '''
        pass

    def _on_command_listbox_motion(self, event):
        '''
        # 커맨드 리스트박스에서 마우스 움직임을 처리합니다.
        # Handles mouse motion in the command listbox.
        '''
        pass

    def _on_command_listbox_leave(self, event):
        '''
        # 커맨드 리스트박스에서 마우스가 벗어났을 때를 처리합니다.
        # Handles the mouse leaving the command listbox.
        '''
        pass

    def _process_command(self, command_text):
        '''
        # 슬래시(/)로 시작하는 명령어를 처리합니다.
        # Processes commands that start with a slash (/).
        '''
        pass

    def _on_command_listbox_select(self, event):
        '''
        # 커맨드 리스트박스에서 항목을 선택했을 때를 처리합니다.
        # Handles item selection in the command listbox.
        '''
        pass

    def _handle_autocomplete(self, event):
        '''
        # 명령어 자동완성을 처리합니다.
        # Handles command autocompletion.
        '''
        pass

    def _on_autocomplete_select(self, selected_arg):
        '''
        # 자동완성 목록에서 항목을 선택했을 때를 처리합니다.
        # Handles item selection from the autocomplete list.
        '''
        pass

    def update_status(self, message, color):
        '''
        # 하단 상태 표시줄의 메시지와 색상을 업데이트합니다.
        # Updates the message and color of the bottom status bar.
        '''
        self.status_label.config(text=message, fg=color)
        self.status_canvas.delete("all")
        self.status_canvas.create_oval(2, 2, 8, 8, fill=color, outline=color)

    def toggle_run_exit(self):
        '''
        # 'Run' 또는 'Kill'/'Exit' 버튼의 동작을 토글합니다.
        # Toggles the action of the 'Run' or 'Kill'/'Exit' button.
        '''
        if self.is_running:
            if self.think_core_process and self.think_core_process.poll() is None: self.think_core_process.terminate()
        else:
            script_path = self.script_path_var.get()
            log_dir = self.log_dir_var.get()

            if not Path(script_path).is_file():
                self.update_status(f"Error: Script not found at {script_path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                return
            
            if not Path(log_dir).is_dir():
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except OSError as e:
                    self.update_status(f"Error: Cannot create log directory: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
                    return

            try: 
                if os.path.exists(PAUSE_FLAG_PATH): os.remove(PAUSE_FLAG_PATH)
            except Exception: pass

            self.is_paused = False
            self.all_logs.clear()
            self.undo_stack.clear()
            self.redo_stack.clear()
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
                command_to_run = [
                    python_executable, 
                    script_path,
                    "--data-dir",
                    DATA_DIR 
                ]
                
                project_root = Path(script_path).resolve().parent.parent.parent
                
                self.think_core_process = subprocess.Popen(
                    command_to_run,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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
        '''
        # 백그라운드 스레드에서 수집된 로그를 주기적으로 처리하여 GUI에 표시합니다.
        # Periodically processes logs collected from the background thread to display in the GUI.
        '''
        messages_processed = False
        try:
            while True:
                action, data = self.log_queue.get_nowait()
                messages_processed = True
                
                msg_text = data.get('message', '')
                level_match = re.search(r"[(TRACE|DEBUG|INFO|WARNING|ERROR|FATAL|THINKING|DATA|AUDIT|SYSTEM|COMMENT|PROGRESS)]", msg_text, re.I)
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
        '''
        # 스크립트 실행이 완료되었을 때 호출됩니다.
        # Called when the script execution is finished.
        '''
        self.is_running = False
        self.last_progress_message = None
        self.update_progress_display("")
        if hasattr(self, 'log_file') and self.log_file and not self.log_file.closed:
            self.log_file.close()
            self.log_file_open = True
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.update_ui_for_state()
        self.filter_logs(scroll_to_end=False)
        self.update_status("Process finished.", self.theme.ACCENT_COLOR)

    def _read_think_core_output(self):
        '''
        # 별도의 스레드에서 실행 중인 스크립트의 표준 출력/오류를 읽습니다.
        # Reads the standard output/error of the running script in a separate thread.
        '''
        def enqueue_output(stream):
            for line in iter(stream.readline, ''):
                line_stripped = line.strip()
                if not line_stripped: continue
                self.log_queue.put(('add', {'message': line_stripped}))
            stream.close()

        stdout_thread = threading.Thread(target=enqueue_output, args=(self.think_core_process.stdout,), daemon=True)
        stderr_thread = threading.Thread(target=enqueue_output, args=(self.think_core_process.stderr,), daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        self.think_core_process.wait()
        self.master.after(0, self._on_run_finish)

    def toggle_pause_resume(self):
        '''
        # 스크립트 실행을 일시정지하거나 재개합니다.
        # Pauses or resumes the script execution.
        '''
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
        '''
        # 로그 디렉토리를 파일 탐색기에서 엽니다.
        # Opens the log directory in the file explorer.
        '''
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
        '''
        # 로그 파일을 열어 내용을 뷰어에 로드합니다.
        # Opens a log file and loads its content into the viewer.
        '''
        log_dir = self.log_dir_var.get()
        if not os.path.isdir(log_dir):
            self.update_status(f"Error: Log directory not found: {log_dir}", self.theme.LOG_LEVEL_COLORS['DELETED']); return
        
        file_path = filedialog.askopenfilename(initialdir=log_dir, title="Select Log File", filetypes=(("Log files", "*.log"), ("all files", "*.*")))
        if not file_path: return

        try:
            self.all_logs, self.undo_stack, self.redo_stack = [], [], []
            log_pattern = re.compile(r"[(TRACE|DEBUG|INFO|PROGRESS|WARNING|ERROR|FATAL|COMMENT|THINKING|DATA|AUDIT|SYSTEM)]")

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
        '''
        # 로그 영역의 폰트 크기를 1 증가시킵니다.
        # Increases the font size of the log area by 1.
        '''
        self.log_font_size += 1; self.configure_tags(); self.filter_logs(scroll_to_end=False)
        self.update_status(f"Font size: {self.log_font_size}", self.theme.ACCENT_COLOR)

    def _decrease_font_size(self):
        '''
        # 로그 영역의 폰트 크기를 1 감소시킵니다 (최소 8).
        # Decreases the font size of the log area by 1 (minimum 8).
        '''
        if self.log_font_size > 8: self.log_font_size -= 1; self.configure_tags(); self.filter_logs(scroll_to_end=False)
        else: self.update_status("Minimum font size reached.", self.theme.DISABLED_TEXT_COLOR)

    def exit_log_view_mode(self):
        '''
        # 로그 파일 보기 모드를 종료하고 초기 상태로 돌아갑니다.
        # Exits the log file viewing mode and returns to the initial state.
        '''
        if self.editor_window_instance and self.editor_window_instance.winfo_exists(): self.editor_window_instance.close_window()
        self.log_file_open = False
        self.all_logs, self.undo_stack, self.redo_stack = [], [], []
        self.log_area.config(state='normal'); self.log_area.delete(1.0, tk.END); self.log_area.config(state='disabled')
        self.current_log_file_path = None
        self.update_ui_for_state()

    def save_log_changes(self):
        '''
        # 로그 파일에 대한 변경사항(추가, 수정, 삭제)을 저장합니다.
        # Saves changes (additions, modifications, deletions) to the log file.
        '''
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
        '''
        # 현재 애플리케이션 상태(실행 중, 일시정지 등)에 따라 UI 요소들을 업데이트합니다.
        # Updates UI elements based on the current application state (running, paused, etc.).
        '''
        if self.is_running:
            self.run_exit_button.config(text="Kill", bg=self.theme.KILL_COLOR, command=self.toggle_run_exit, state="normal")
            self._bind_button_effects(self.run_exit_button, self.theme.KILL_COLOR, self.theme.KILL_HOVER_COLOR)
            if self.is_paused:
                if self.undo_stack:
                    self.pause_resume_button.config(text="Save", bg=self.theme.PRIMARY_COLOR, command=self.save_log_changes, state="normal", fg="white")
                    self._bind_button_effects(self.pause_resume_button, self.theme.PRIMARY_COLOR, self.theme.PRIMARY_HOVER_COLOR)
                else:
                    self.pause_resume_button.config(text="Resume", bg=self.theme.SUCCESS_COLOR, command=self.toggle_pause_resume, state="normal", fg="white")
                    self._bind_button_effects(self.pause_resume_button, self.theme.SUCCESS_COLOR, self.theme.SUCCESS_HOVER_COLOR)
                self.comment_entry.config(state="normal", fg=self.theme.TEXT_COLOR); self.comment_entry.delete(1.0, tk.END)
                self.send_button.config(state="normal", fg=self.theme.ACCENT_COLOR); self.command_button.config(state="normal", fg=self.theme.ACCENT_COLOR)
                self.update_status("Paused. Editing enabled.", self.theme.ACCENT_COLOR)
            else:
                self.pause_resume_button.config(text="Pause", bg=self.theme.WARNING_COLOR, command=self.toggle_pause_resume, state="normal", fg="white")
                self._bind_button_effects(self.pause_resume_button, self.theme.WARNING_COLOR, self.theme.WARNING_HOVER_COLOR)
                self.comment_entry.delete(1.0, tk.END); self.comment_entry.insert(tk.END, "Editing is only available in Paused or Stopped state.")
                self.comment_entry.config(state="disabled", fg=self.theme.DISABLED_TEXT_COLOR)
                self.send_button.config(state="disabled", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR)
                self.command_button.config(state="disabled", fg=self.theme.DISABLED_TEXT_COLOR)
                self.update_status("Running...", self.theme.SUCCESS_COLOR)
        elif self.log_file_open: 
            self.run_exit_button.config(text="Exit", bg=self.theme.KILL_COLOR, command=self.exit_log_view_mode, state="normal")
            self._bind_button_effects(self.run_exit_button, self.theme.KILL_COLOR, self.theme.KILL_HOVER_COLOR)
            self.pause_resume_button.config(command=self.save_log_changes, text="Save", state="normal" if self.undo_stack else "disabled")
            if self.undo_stack:
                self.pause_resume_button.config(bg=self.theme.PRIMARY_COLOR, fg="white")
                self._bind_button_effects(self.pause_resume_button, self.theme.PRIMARY_COLOR, self.theme.PRIMARY_HOVER_COLOR)
            else: self.pause_resume_button.config(**self.theme.DISABLED_BUTTON_STYLE)
            self.comment_entry.config(state="normal", fg=self.theme.TEXT_COLOR); self.comment_entry.delete(1.0, tk.END)
            self.send_button.config(state="normal", fg=self.theme.ACCENT_COLOR); self.command_button.config(state="normal", fg=self.theme.ACCENT_COLOR)
            if not self.undo_stack and self.current_log_file_path and "undo" not in self.status_label.cget("text").lower() and "redo" not in self.status_label.cget("text").lower():
                self.update_status(f"Viewing: {os.path.basename(self.current_log_file_path)}", self.theme.ACCENT_COLOR)
        else:
            self.run_exit_button.config(text="Run", bg=self.theme.SUCCESS_COLOR, command=self.toggle_run_exit, state="normal")
            self._bind_button_effects(self.run_exit_button, self.theme.SUCCESS_COLOR, self.theme.SUCCESS_HOVER_COLOR)
            self.pause_resume_button.config(text="Pause", state="disabled", **self.theme.DISABLED_BUTTON_STYLE)
            self.comment_entry.delete(1.0, tk.END)
            self.comment_entry.insert(tk.END, "Idle: Run or open a log file to start.")
            self.comment_entry.config(state="disabled", fg=self.theme.DISABLED_TEXT_COLOR)
            self.send_button.config(state="disabled", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR)
            self.command_button.config(state="disabled", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR)
            self.update_status("Idle", self.theme.DISABLED_TEXT_COLOR)

    def _bind_button_effects(self, button, default_bg, hover_bg):
        '''
        # 버튼에 마우스 오버 및 클릭 효과를 바인딩합니다.
        # Binds mouse hover and click effects to a button.
        '''
        button.original_bg, button.hover_bg = default_bg, hover_bg
        def on_enter(event): 
            if button['state'] == 'normal': self._animate_color(button, button['bg'], button.hover_bg)
        def on_leave(event):
            if button['state'] == 'normal': self._animate_color(button, button['bg'], button.original_bg)
        button.bind("<Enter>", on_enter, add="+ "); button.bind("<Leave>", on_leave, add="+ ")
