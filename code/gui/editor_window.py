
import tkinter as tk
from tkinter import Button, Label
import re
import copy
from datetime import datetime
from typing import TYPE_CHECKING
from .gui_widgets import StyledButton

if TYPE_CHECKING:
    from .log_display import LogDisplay
    from .theme import Theme

class EditorWindow(tk.Toplevel):
    """
    # A pop-up window for creating and modifying log entries.
    # 로그 항목을 생성하고 수정하기 위한 팝업 창 클래스입니다.
    """
    def __init__(self, master_app: 'LogDisplay', log_index: int | None):
        """
        # Initializes the EditorWindow instance.
        # EditorWindow 인스턴스를 초기화합니다.

        # Args:
        #     master_app (LogDisplay): The main application instance.
        #                           (메인 애플리케이션 인스턴스입니다.)
        #     log_index (int | None): The index of the log to edit. If None, starts in 'Add' mode.
        #                           (편집할 로그의 인덱스입니다. None이면 'Add' 모드로 시작합니다.)
        """
        super().__init__(master_app.master)
        self.master_app = master_app
        self.theme: 'Theme' = master_app.theme
        self.title("Edit Log Entry")
        self.geometry("800x600")
        self.configure(bg=self.theme.BG_COLOR)
        self.transient(master_app.master)
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.selected_level_var = tk.StringVar()
        self.is_add_mode = tk.BooleanVar()
        self.editor_font_size = tk.IntVar(value=self.master_app.log_font_size)
        self.current_log_index = None
        
        self._create_widgets()
        self.update_content(log_index)

    def _apply_theme(self):
        """
        # Applies the current theme to all widgets in the editor window.
        # 현재 테마를 에디터 창의 모든 위젯에 적용합니다.
        """
        self.theme = self.master_app.theme
        self.configure(bg=self.theme.BG_COLOR)

        self.top_frame.config(bg=self.theme.BG_COLOR)
        self.log_type_label.config(bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR)

        self.picker_frame.config(bg=self.theme.ENTRY_BG_COLOR)
        self.level_label.config(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR)
        self.arrow_label.config(bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR)

        self.font_decrease_btn.update_style(bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR)
        self.font_increase_btn.update_style(bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR)

        self.apply_button.update_style(bg=self.theme.SUCCESS_COLOR, hover_color=self.theme.SUCCESS_HOVER_COLOR)
        self.add_button.update_style(bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR)
        self.edit_button.update_style(bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR)

        self.editor_text.config(
            bg=self.theme.LOG_AREA_BG_COLOR, 
            fg=self.theme.TEXT_COLOR, 
            insertbackground=self.theme.INSERT_CURSOR_COLOR
        )

    def _create_widgets(self):
        """
        # Creates and places all UI widgets for the editor window.
        # 에디터 창의 모든 UI 위젯을 생성하고 배치합니다.
        """
        self.top_frame = tk.Frame(self, bg=self.theme.BG_COLOR)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.log_type_label = Label(self.top_frame, text="Log Type:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10))
        self.log_type_label.pack(side="left", padx=(5,5))

        self.picker_frame = tk.Frame(self.top_frame, bg=self.theme.ENTRY_BG_COLOR, cursor="hand2")
        self.picker_frame.pack(side="left", padx=(0, 20), ipady=4, ipadx=5)

        self.level_label = Label(self.picker_frame, textvariable=self.selected_level_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10))
        self.level_label.pack(side="left", padx=(5, 10))

        self.arrow_label = Label(self.picker_frame, text="▼", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_LOG, 8))
        self.arrow_label.pack(side="left", padx=(0, 5))

        for widget in [self.picker_frame, self.level_label, self.arrow_label]: 
            widget.bind("<Button-1>", self._show_log_level_picker)

        font_frame = tk.Frame(self.top_frame, bg=self.theme.BG_COLOR)
        font_frame.pack(side="left")

        self.font_decrease_btn = StyledButton(font_frame, parent_frame=self.master_app, text="A-", command=self._decrease_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR, padx=5)
        self.font_decrease_btn.pack(side="left")
        self.font_increase_btn = StyledButton(font_frame, parent_frame=self.master_app, text="A+", command=self._increase_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR, padx=5)
        self.font_increase_btn.pack(side="left")

        button_container = tk.Frame(self.top_frame, bg=self.theme.BG_COLOR)
        button_container.pack(side="right")

        self.apply_button = StyledButton(button_container, parent_frame=self.master_app, text="Apply", command=self._save_and_close, **self.theme.BUTTON_STYLE, bg=self.theme.SUCCESS_COLOR, hover_color=self.theme.SUCCESS_HOVER_COLOR)
        self.apply_button.pack(side="right")

        mode_frame = tk.Frame(button_container, bg=self.theme.BG_COLOR)
        mode_frame.pack(side="right", padx=10)

        self.add_button = StyledButton(mode_frame, parent_frame=self.master_app, text="ADD", command=self.switch_to_add_mode, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR, font=(self.theme.FONT_FAMILY_UI, 9))
        self.add_button.pack(side="left")

        self.edit_button = StyledButton(mode_frame, parent_frame=self.master_app, text="EDIT", command=self.switch_to_edit_mode, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, hover_color=self.theme.HOVER_COLOR, font=(self.theme.FONT_FAMILY_UI, 9))
        self.edit_button.pack(side="left")

        self.editor_text = tk.Text(self, wrap=tk.WORD, font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()), bg=self.theme.LOG_AREA_BG_COLOR, fg=self.theme.TEXT_COLOR, insertbackground=self.theme.INSERT_CURSOR_COLOR, bd=0, highlightthickness=0, padx=5, pady=5, undo=True)
        self.editor_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

    def update_content(self, log_index: int | None):
        """
        # Fills the editor with content from a specific log entry or clears it for a new one.
        # 에디터의 내용을 특정 로그 항목으로 채우거나 새 항목을 위해 비웁니다.

        # Args:
        #     log_index (int | None): The index of the log to display. If None, sets up for adding a new log.
        #                           (표시할 로그의 인덱스. None이면 새 로그 추가 모드로 설정됩니다.)
        """
        self.current_log_index = log_index
        if log_index is not None and 0 <= log_index < len(self.master_app.all_logs):
            # Edit mode: Fill with existing log data.
            # 편집 모드: 기존 로그 데이터로 채웁니다.
            original_log = self.master_app.all_logs[log_index]
            message_only = re.sub(r'^\s*\[\d{2}:\d{2}:\d{2}\]\s*\[[A-Z_]+\]\s*', '', original_log['message'])
            self.editor_text.delete(1.0, tk.END)
            self.editor_text.insert(tk.END, message_only)
            self.selected_level_var.set(original_log.get('level', 'COMMENT'))
            self._set_mode(is_add=False)
        else:
            # Add mode: Clear the editor.
            # 추가 모드: 에디터를 비웁니다.
            self.editor_text.delete(1.0, tk.END)
            self.selected_level_var.set('COMMENT')
            self._set_mode(is_add=True)
        self.editor_text.edit_reset()
        
    def switch_to_add_mode(self):
        """
        # Switches to ADD mode and clears the content.
        # ADD 모드로 전환하고 내용을 지웁니다.
        """
        if self.is_add_mode.get():
            return
        self.update_content(None)

    def switch_to_edit_mode(self):
        """
        # Switches to EDIT mode and loads the selected log content. Does nothing if no log is selected.
        # EDIT 모드로 전환하고 선택된 로그 내용을 불러옵니다. 선택된 로그가 없으면 실행되지 않습니다.
        """
        selected_index = self.master_app.selected_log_abs_index
        if selected_index is None:
            self.master_app.update_status("Select a log line to switch to Edit mode.", self.theme.LOG_LEVEL_COLORS['WARNING'])
            return
        
        if not self.is_add_mode.get() and self.current_log_index == selected_index:
            return
            
        self.update_content(selected_index)

    def _set_mode(self, is_add: bool):
        """
        # Sets the editor's mode ('Add' or 'Edit') and updates the UI accordingly.
        # 에디터의 모드('Add' 또는 'Edit')를 설정하고 UI를 업데이트합니다.

        # Args:
        #     is_add (bool): True for 'Add' mode, False for 'Edit' mode.
        #                  (True이면 'Add' 모드, False이면 'Edit' 모드로 설정합니다.)
        """
        self.is_add_mode.set(is_add)
        if is_add:
            self.title("Add New Log Entry")
            self.add_button.update_style(bg=self.theme.LOG_LEVEL_COLORS['ADDED'], hover_color=self.theme.LOG_LEVEL_COLORS['ADDED'], fg=self.theme.BUTTON_STYLE['fg'])
            self.edit_button.update_style(bg=self.theme.WIDGET_BG_COLOR, hover_color=self.theme.HOVER_COLOR, fg=self.theme.TEXT_COLOR)
        else:
            self.title("Edit Log Entry")
            self.add_button.update_style(bg=self.theme.WIDGET_BG_COLOR, hover_color=self.theme.HOVER_COLOR, fg=self.theme.TEXT_COLOR)
            self.edit_button.update_style(bg=self.theme.LOG_LEVEL_COLORS['MODIFIED'], hover_color=self.theme.LOG_LEVEL_COLORS['MODIFIED'], fg=self.theme.BUTTON_STYLE['fg'])
        self.editor_text.focus_set()

    def _save_and_close(self):
        """
        # Saves the current content of the editor and closes the window.
        # 에디터의 현재 내용을 저장하고 창을 닫습니다.
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
            # In 'Add' mode, create a new log entry and insert it into the main log list.
            # 'Add' 모드일 경우, 새 로그 항목을 생성하고 메인 로그 목록에 삽입합니다.
            new_log = {'message': formatted_message, 'level': selected_level, 'state': 'ADDED'}
            insert_pos = self.master_app.selected_log_abs_index + 1 if self.master_app.selected_log_abs_index is not None else len(self.master_app.all_logs)
            self.master_app.all_logs.insert(insert_pos, new_log)
            self.master_app._record_action('add', {'line_num': insert_pos, 'log_entry': new_log})
            self.master_app.update_status("New log entry added.", self.master_app.theme.LOG_LEVEL_COLORS['ADDED'])
        else:
            # In 'Edit' mode, update the existing log entry.
            # 'Edit' 모드일 경우, 기존 로그 항목을 업데이트합니다.
            if self.current_log_index is not None and 0 <= self.current_log_index < len(self.master_app.all_logs):
                line_num = self.current_log_index
                original_log = copy.deepcopy(self.master_app.all_logs[line_num])
                self.master_app.all_logs[line_num].update({'message': formatted_message, 'level': selected_level, 'state': 'MODIFIED'})
                self.master_app._record_action('edit', {'line_num': line_num, 'original_log': original_log})
                self.master_app.update_status(f"Log line {line_num + 1} updated.", self.master_app.theme.LOG_LEVEL_COLORS['MODIFIED'])
            else:
                self.master_app.update_status("Error: Log to edit no longer exists.", self.master_app.theme.LOG_LEVEL_COLORS['DELETED'])
        
        self.master_app._perform_search_and_filter_logs(scroll_to_end=False)
        self.close_window()

    def _show_log_level_picker(self, event):
        """
        # Displays a dropdown menu to select the log level.
        # 로그 레벨을 선택할 수 있는 드롭다운 메뉴를 표시합니다.
        """
        widget = event.widget.master if not isinstance(event.widget, tk.Frame) else event.widget
        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)
        x, y = widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height()
        
        listbox = tk.Listbox(popup, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, selectbackground=self.theme.ACCENT_COLOR, 
                             selectforeground=self.theme.BG_COLOR, highlightthickness=0, relief="solid", bd=1, font=(self.theme.FONT_FAMILY_UI, 10))
        log_types = self.master_app.autocomplete_commands.get('/add', [])
        for level in log_types:
            listbox.insert(tk.END, level)
        listbox.pack(fill="both", expand=True)
        
        listbox.bind("<<ListboxSelect>>", lambda e: (self.selected_level_var.set(listbox.get(listbox.curselection())), popup.destroy()))
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        
        popup.geometry(f"120x{len(log_types) * 24}+{x}+{y}")
        popup.focus_set()

    def _increase_font_size(self):
        """
        # Increases the editor's font size by 1.
        # 에디터의 폰트 크기를 1 증가시킵니다.
        """
        self.editor_font_size.set(self.editor_font_size.get() + 1)
        self.editor_text.config(font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()))

    def _decrease_font_size(self):
        """
        # Decreases the editor's font size by 1 (minimum 8).
        # 에디터의 폰트 크기를 1 감소시킵니다 (최소 8).
        """
        if self.editor_font_size.get() > 8:
            self.editor_font_size.set(self.editor_font_size.get() - 1)
            self.editor_text.config(font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()))

    def close_window(self):
        """
        # Closes the editor window and resets the reference in the main app.
        # 에디터 창을 닫고 메인 앱의 참조를 초기화합니다.
        """
        self.master_app.editor_window_instance = None
        self.destroy()
