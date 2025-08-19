# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\editor_window.py
"""
# EditorWindow 클래스를 정의합니다. 이 클래스는 로그 항목을 추가하거나 편집하기 위한 Toplevel 창입니다.
# Defines the EditorWindow class, a Toplevel window for adding or editing log entries.

# 이 모듈은 사용자가 새 로그 메시지를 작성하거나 기존 메시지를 수정할 수 있는 전용 UI를 제공합니다.
# 'Add'와 'Edit' 두 가지 모드로 작동합니다. 이 창은 메인 LogDisplay 애플리케이션에서 실행되며,
# 로그 데이터를 변경하기 위해 메인 앱과 상호작용합니다.
# This module provides a dedicated UI for users to compose new log messages or
# modify existing ones. It operates in two modes: 'Add' and 'Edit'. The window
# is launched from the main LogDisplay application and interacts with it to
# apply changes to the log data.
"""

import tkinter as tk
from tkinter import Button, Label
import re
import copy
from datetime import datetime
from typing import TYPE_CHECKING

# 타입 체킹 시에만 LogDisplay와 Theme 클래스를 임포트하여 순환 참조를 방지합니다.
# Import LogDisplay and Theme classes only for type checking to prevent circular imports.
if TYPE_CHECKING:
    from .log_display import LogDisplay
    from .theme import Theme

class EditorWindow(tk.Toplevel):
    """
    # 로그 항목을 생성하고 수정하기 위한 팝업 창 클래스입니다.
    # A pop-up window for creating and modifying log entries.
    """
    def __init__(self, master_app: 'LogDisplay', log_index: int | None):
        """
        # EditorWindow 인스턴스를 초기화합니다.
        # Initializes the EditorWindow instance.

        # Args:
        #     master_app (LogDisplay): 메인 애플리케이션 인스턴스입니다. (The main application instance.)
        #     log_index (int | None): 편집할 로그의 인덱스입니다. None이면 'Add' 모드로 시작합니다. (The index of the log to edit. If None, starts in 'Add' mode.)
        """
        super().__init__(master_app.master)
        self.master_app = master_app  # 메인 애플리케이션 참조 (Reference to the main application)
        self.theme: 'Theme' = master_app.theme  # 테마 객체 참조 (Reference to the theme object)
        self.title("Edit Log Entry")  # 창 제목 설정 (Set window title)
        self.geometry("800x600")  # 창 크기 설정 (Set window size)
        self.configure(bg=self.theme.BG_COLOR)  # 배경색 설정 (Set background color)
        self.transient(master_app.master)  # 메인 창 위에 표시되도록 설정 (Set to appear on top of the main window)
        self.protocol("WM_DELETE_WINDOW", self.close_window)  # 닫기 버튼 콜백 설정 (Set close button callback)

        # 그리드 레이아웃 설정 (Configure grid layout)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 위젯에서 사용할 변수들 (Variables for widgets)
        self.selected_level_var = tk.StringVar()  # 선택된 로그 레벨 저장 (Stores the selected log level)
        self.is_add_mode = tk.BooleanVar()  # 현재 'Add' 모드인지 여부 저장 (Stores whether it's in 'Add' mode)
        self.editor_font_size = tk.IntVar(value=self.master_app.log_font_size)  # 에디터 폰트 크기 (Editor font size)
        self.current_log_index = None  # 현재 편집 중인 로그의 인덱스 (Index of the log currently being edited)
        
        self._create_widgets()  # 위젯 생성 (Create widgets)
        self.update_content(log_index)  # 내용 업데이트 (Update content)

    def _create_widgets(self):
        """
        # 에디터 창의 모든 UI 위젯을 생성하고 배치합니다.
        # Creates and places all UI widgets for the editor window.
        """
        # --- 상단 프레임 (Top Frame) ---
        top_frame = tk.Frame(self, bg=self.theme.BG_COLOR)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # 로그 타입 선택기 (Log Type Picker)
        Label(top_frame, text="Log Type:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10)).pack(side="left", padx=(5,5))
        picker_frame = tk.Frame(top_frame, bg=self.theme.ENTRY_BG_COLOR, cursor="hand2")
        picker_frame.pack(side="left", padx=(0, 20), ipady=4, ipadx=5)
        level_label = Label(picker_frame, textvariable=self.selected_level_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10))
        level_label.pack(side="left", padx=(5, 10))
        arrow_label = Label(picker_frame, text="▼", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_LOG, 8))
        arrow_label.pack(side="left", padx=(0, 5))
        for widget in [picker_frame, level_label, arrow_label]: 
            widget.bind("<Button-1>", self._show_log_level_picker)
            
        # 폰트 크기 조절 버튼 (Font Size Control Buttons)
        font_frame = tk.Frame(top_frame, bg=self.theme.BG_COLOR)
        font_frame.pack(side="left")
        Button(font_frame, text="A-", command=self._decrease_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5).pack(side="left")
        Button(font_frame, text="A+", command=self._increase_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5).pack(side="left")
        
        # 우측 버튼 컨테이너 (Right Button Container)
        button_container = tk.Frame(top_frame, bg=self.theme.BG_COLOR)
        button_container.pack(side="right")

        # 적용 버튼 (Apply Button)
        apply_button = Button(button_container, text="Apply", command=self._save_and_close, **self.theme.BUTTON_STYLE)
        apply_button.pack(side="right")
        apply_button.config(bg=self.theme.SUCCESS_COLOR, activebackground=self.theme.SUCCESS_HOVER_COLOR)
        self.master_app._bind_button_effects(apply_button, self.theme.SUCCESS_COLOR, self.theme.SUCCESS_HOVER_COLOR)

        # 모드 전환 프레임 (Mode Switch Frame)
        mode_frame = tk.Frame(button_container, bg=self.theme.BG_COLOR)
        mode_frame.pack(side="right", padx=10)

        Label(mode_frame, text="Mode:", bg=self.theme.BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10)).pack(side="left")

        self.mode_badge_label = Label(mode_frame, text="", font=(self.theme.FONT_FAMILY_UI, 9, "bold"), fg="white", padx=5, pady=2)
        self.mode_badge_label.pack(side="left", padx=5)

        switch_button = Button(mode_frame, text="Switch", command=self._toggle_add_edit_mode, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", activebackground=self.theme.CLICK_COLOR, font=(self.theme.FONT_FAMILY_UI, 9))
        switch_button.pack(side="left")
        self.master_app._bind_button_effects(switch_button, self.theme.WIDGET_BG_COLOR, self.theme.HOVER_COLOR)
        
        # 텍스트 에디터 (Text Editor)
        self.editor_text = tk.Text(self, wrap=tk.WORD, font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()), bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, bd=0, highlightthickness=0, padx=5, pady=5, undo=True)
        self.editor_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

    def update_content(self, log_index: int | None):
        """
        # 에디터의 내용을 특정 로그 항목으로 채우거나 비웁니다.
        # Fills the editor with content from a specific log entry or clears it.

        # Args:
        #     log_index (int | None): 표시할 로그의 인덱스. None이면 새 로그 추가 모드로 설정됩니다.
        #                           (The index of the log to display. If None, sets up for adding a new log.)
        """
        self.current_log_index = log_index
        # 'Edit' 모드: 유효한 로그 인덱스가 주어진 경우
        # 'Edit' mode: If a valid log index is given
        if log_index is not None and 0 <= log_index < len(self.master_app.all_logs):
            original_log = self.master_app.all_logs[log_index]
            # 정규식을 사용하여 타임스탬프와 로그 레벨 부분을 제외한 순수 메시지만 추출합니다.
            # Use regex to extract only the pure message, excluding the timestamp and log level parts.
            message_only = re.sub(r"^\s*\[\d{2}:\d{2}:\d{2}\]\s*\[(.*?)(?:\s*)\]\s*", '', original_log['message'])
            self.editor_text.delete(1.0, tk.END)
            self.editor_text.insert(tk.END, message_only)
            self.selected_level_var.set(original_log.get('level', 'COMMENT'))
            self._set_mode(is_add=False)
        # 'Add' 모드: 로그 인덱스가 None인 경우
        # 'Add' mode: If log index is None
        else:
            self.editor_text.delete(1.0, tk.END)
            self.selected_level_var.set('COMMENT')
            self._set_mode(is_add=True)
        # undo/redo 스택을 초기화합니다.
        # Reset the undo/redo stack.
        self.editor_text.edit_reset()

    def _set_mode(self, is_add: bool):
        """
        # 에디터의 모드('Add' 또는 'Edit')를 설정하고 UI를 업데이트합니다.
        # Sets the editor's mode ('Add' or 'Edit') and updates the UI accordingly.

        # Args:
        #     is_add (bool): True이면 'Add' 모드, False이면 'Edit' 모드로 설정합니다.
        #                  (True for 'Add' mode, False for 'Edit' mode.)
        """
        self.is_add_mode.set(is_add)
        if is_add:
            self.mode_badge_label.config(text="ADD", bg=self.theme.LOG_LEVEL_COLORS['ADDED'])
            self.title("Add New Log Entry")
        else:
            self.mode_badge_label.config(text="EDIT", bg=self.theme.LOG_LEVEL_COLORS['MODIFIED'])
            self.title("Edit Log Entry")
        self.editor_text.focus_set()

    def _toggle_add_edit_mode(self):
        """
        # 'Add' 모드와 'Edit' 모드 사이를 전환합니다.
        # Toggles between 'Add' and 'Edit' modes.
        """
        if self.is_add_mode.get():
            # 현재 'Add' 모드이면, 메인 앱에서 선택된 로그를 불러와 'Edit' 모드로 전환합니다.
            # If in 'Add' mode, switch to 'Edit' mode with the log selected in the main app.
            self.update_content(self.master_app.selected_log_abs_index)
        else:
            # 현재 'Edit' 모드이면, 에디터를 비워 'Add' 모드로 전환합니다.
            # If in 'Edit' mode, switch to 'Add' mode by clearing the editor.
            self.update_content(None)

    def _save_and_close(self):
        """
        # 에디터의 현재 내용을 저장하고 창을 닫습니다.
        # Saves the current content of the editor and closes the window.
        """
        content = self.editor_text.get(1.0, tk.END).strip()
        if not content:
            self.master_app.update_status("Editor content is empty.", self.master_app.theme.LOG_LEVEL_COLORS['DELETED'])
            self.close_window()
            return

        timestamp = datetime.now().strftime('%H:%M:%S')
        selected_level = self.selected_level_var.get().upper()
        formatted_message = f"[{timestamp}] [{selected_level}] {content}"

        if self.is_add_mode.get():
            # 'Add' 모드일 경우, 새 로그 항목을 생성하고 메인 로그 목록에 삽입합니다.
            # In 'Add' mode, create a new log entry and insert it into the main log list.
            new_log = {'message': formatted_message, 'level': selected_level, 'state': 'ADDED'}
            insert_pos = self.master_app.selected_log_abs_index + 1 if self.master_app.selected_log_abs_index is not None else len(self.master_app.all_logs)
            self.master_app.all_logs.insert(insert_pos, new_log)
            self.master_app._record_action('add', {'line_num': insert_pos, 'log_entry': new_log})
            self.master_app.update_status("New log entry added.", self.master_app.theme.LOG_LEVEL_COLORS['ADDED'])
        else:
            # 'Edit' 모드일 경우, 기존 로그 항목을 업데이트합니다.
            # In 'Edit' mode, update the existing log entry.
            if self.current_log_index is not None and 0 <= self.current_log_index < len(self.master_app.all_logs):
                line_num = self.current_log_index
                original_log = copy.deepcopy(self.master_app.all_logs[line_num])
                self.master_app.all_logs[line_num].update({'message': formatted_message, 'level': selected_level, 'state': 'MODIFIED'})
                self.master_app._record_action('edit', {'line_num': line_num, 'original_log': original_log})
                self.master_app.update_status(f"Log line {line_num + 1} updated.", self.master_app.theme.LOG_LEVEL_COLORS['MODIFIED'])
            else:
                self.master_app.update_status("Error: Log to edit no longer exists.", self.master_app.theme.LOG_LEVEL_COLORS['DELETED'])
        
        self.master_app.filter_logs(scroll_to_end=False)
        self.close_window()

    def _show_log_level_picker(self, event):
        """
        # 로그 레벨을 선택할 수 있는 드롭다운 메뉴를 표시합니다.
        # Displays a dropdown menu to select the log level.
        """
        widget = event.widget.master if not isinstance(event.widget, tk.Frame) else event.widget
        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)  # 창 테두리 제거 (Remove window border)
        x, y = widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height()
        
        listbox = tk.Listbox(popup, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, selectbackground=self.theme.ACCENT_COLOR, 
                             selectforeground=self.theme.BG_COLOR, highlightthickness=0, relief="solid", bd=1, font=(self.theme.FONT_FAMILY_UI, 10))
        log_types = self.master_app.autocomplete_commands.get('/add', [])
        for level in log_types:
            listbox.insert(tk.END, level)
        listbox.pack(fill="both", expand=True)
        
        # 항목 선택 시 변수 업데이트 및 팝업 닫기
        # Update variable and close popup on item selection
        listbox.bind("<<ListboxSelect>>", lambda e: (self.selected_level_var.set(listbox.get(listbox.curselection())), popup.destroy()))
        # 포커스를 잃으면 팝업 닫기
        # Close popup on focus out
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        
        popup.geometry(f"120x{len(log_types) * 24}+{x}+{y}")
        popup.focus_set()

    def _increase_font_size(self):
        """
        # 에디터의 폰트 크기를 1 증가시킵니다.
        # Increases the editor's font size by 1.
        """
        self.editor_font_size.set(self.editor_font_size.get() + 1)
        self.editor_text.config(font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()))

    def _decrease_font_size(self):
        """
        # 에디터의 폰트 크기를 1 감소시킵니다 (최소 8).
        # Decreases the editor's font size by 1 (minimum 8).
        """
        if self.editor_font_size.get() > 8:
            self.editor_font_size.set(self.editor_font_size.get() - 1)
            self.editor_text.config(font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()))

    def close_window(self):
        """
        # 에디터 창을 닫고 메인 앱의 참조를 초기화합니다.
        # Closes the editor window and resets the reference in the main app.
        """
        self.master_app.editor_window_instance = None
        self.destroy()
