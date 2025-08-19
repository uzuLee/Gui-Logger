# E:\projectFiles\programming\.gemini-cli\glen_prototype\src\utils\logging_gui\gui\editor_window.py
"""
Defines the EditorWindow class, a Toplevel window for adding or editing log entries.

This module provides a dedicated UI for users to compose new log messages or
modify existing ones. It operates in two modes: 'Add' and 'Edit'. The window
is launched from the main LogDisplay application and interacts with it to
apply changes to the log data.
"""

import tkinter as tk
from tkinter import Button, Label
import re
import copy
from datetime import datetime
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports at runtime,
# allowing for type hints from modules that also import this one.
if TYPE_CHECKING:
    from .log_display import LogDisplay
    from .theme import Theme

class EditorWindow(tk.Toplevel):
    """
    A pop-up window for creating and modifying log entries.

    This window provides a text area for log content, a level selector,
    and controls for saving changes. It can be initialized with a specific
    log entry for editing or as a blank slate for adding a new entry.
    """
    def __init__(self, master_app: 'LogDisplay', log_index: int | None):
        """
        Initializes the EditorWindow.

        Args:
            master_app: The main LogDisplay application instance.
            log_index: The absolute index of the log entry to be edited.
                       If None, the window starts in 'Add' mode.
        """
        super().__init__(master_app.master)
        self.master_app = master_app
        self.theme: 'Theme' = master_app.theme
        self.title("Edit Log Entry")
        self.geometry("800x600")
        self.configure(bg=self.theme.BG_COLOR)
        self.transient(master_app.master)  # Keep this window on top of the main app
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        # Configure grid layout to allow the text editor to expand
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # --- State Variables ---
        self.selected_level_var = tk.StringVar()
        self.add_edit_button_text = tk.StringVar()
        self.is_add_mode = tk.BooleanVar()
        self.editor_font_size = tk.IntVar(value=self.master_app.log_font_size)
        self.current_log_index = None
        
        self._create_widgets()
        self.update_content(log_index)

    def _create_widgets(self):
        """Creates and lays out all the widgets in the editor window."""
        # --- Top Control Frame ---
        top_frame = tk.Frame(self, bg=self.theme.BG_COLOR)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Log Level Picker
        Label(top_frame, text="Log Type:", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10)).pack(side="left", padx=(5,5))
        picker_frame = tk.Frame(top_frame, bg=self.theme.ENTRY_BG_COLOR, cursor="hand2")
        picker_frame.pack(side="left", padx=(0, 20), ipady=4, ipadx=5)
        level_label = Label(picker_frame, textvariable=self.selected_level_var, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10))
        level_label.pack(side="left", padx=(5, 10))
        arrow_label = Label(picker_frame, text="▼", bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_LOG, 8))
        arrow_label.pack(side="left", padx=(0, 5))
        for widget in [picker_frame, level_label, arrow_label]: 
            widget.bind("<Button-1>", self._show_log_level_picker)
            
        # Font Size Controls
        font_frame = tk.Frame(top_frame, bg=self.theme.BG_COLOR)
        font_frame.pack(side="left")
        Button(font_frame, text="A-", command=self._decrease_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5).pack(side="left")
        Button(font_frame, text="A+", command=self._increase_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5).pack(side="left")
        
        # Main Action Buttons (Apply, Toggle Mode)
        button_container = tk.Frame(top_frame, bg=self.theme.BG_COLOR)
        button_container.pack(side="right")
        self.toggle_button = Button(button_container, textvariable=self.add_edit_button_text, command=self._toggle_add_edit_mode, bg=self.theme.PRIMARY_COLOR, fg="white", relief="flat", padx=10, pady=5)
        self.toggle_button.pack(side="right", padx=(5,0))
        apply_button = Button(button_container, text="Apply", command=self._save_and_close, bg=self.theme.SUCCESS_COLOR, fg="white", relief="flat", padx=10, pady=5)
        apply_button.pack(side="right")
        
        # --- Main Text Editor ---
        self.editor_text = tk.Text(self, wrap=tk.WORD, font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()), bg="#121212", fg=self.theme.TEXT_COLOR, insertbackground="white", bd=0, highlightthickness=0, padx=5, pady=5, undo=True)
        self.editor_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

    def update_content(self, log_index: int | None):
        """
        Populates the editor with log data or prepares it for a new entry.

        Args:
            log_index: The index of the log to load. If None, clears the
                       editor for 'Add' mode.
        """
        self.current_log_index = log_index
        # If a valid log index is provided, load its content for editing.
        if log_index is not None and 0 <= log_index < len(self.master_app.all_logs):
            original_log = self.master_app.all_logs[log_index]
            # Use regex to strip the timestamp and level prefix from the message.
            message_only = re.sub(r"^\s*\[\d{2}:\d{2}:\d{2}\]\s*\[(.*?)(\s*)\]\s*", '', original_log['message'])
            self.editor_text.delete(1.0, tk.END)
            self.editor_text.insert(tk.END, message_only)
            self.selected_level_var.set(original_log.get('level', 'COMMENT'))
            self._set_mode(is_add=False)
        # Otherwise, set up the window for adding a new log.
        else:
            self.editor_text.delete(1.0, tk.END)
            self.selected_level_var.set('COMMENT')
            self._set_mode(is_add=True)
        self.editor_text.edit_reset() # Clear the undo/redo history for the text widget

    def _set_mode(self, is_add: bool):
        """
        Configures the UI for either 'Add' or 'Edit' mode.

        Args:
            is_add: True to configure for 'Add' mode, False for 'Edit' mode.
        """
        self.is_add_mode.set(is_add)
        self.add_edit_button_text.set("Switch to Add Mode" if not is_add else "Switch to Edit Mode")
        self.toggle_button.config(bg=self.theme.LOG_LEVEL_COLORS['ADDED'] if not is_add else self.theme.LOG_LEVEL_COLORS['MODIFIED'])
        self.title("Edit Log Entry" if not is_add else "Add New Log Entry")
        self.editor_text.focus_set()

    def _toggle_add_edit_mode(self):
        """Switches the editor between 'Add' and 'Edit' modes."""
        if self.is_add_mode.get():
            # If currently in 'Add' mode, switch to 'Edit' mode using the selected log.
            self.update_content(self.master_app.selected_log_abs_index)
        else:
            # If currently in 'Edit' mode, switch to 'Add' mode.
            self.update_content(None)

    def _save_and_close(self):
        """Saves the content as a new or modified log and closes the window."""
        content = self.editor_text.get(1.0, tk.END).strip()
        if not content:
            self.master_app.update_status("Editor content is empty.", self.master_app.theme.LOG_LEVEL_COLORS['DELETED'])
            self.close_window()
            return

        # Format the new log message with timestamp and selected level.
        timestamp = datetime.now().strftime('%H:%M:%S')
        selected_level = self.selected_level_var.get().upper()
        formatted_message = f"[{timestamp}] [{selected_level}] {content}"

        if self.is_add_mode.get():
            # --- Add new log entry ---
            new_log = {'message': formatted_message, 'level': selected_level, 'state': 'ADDED'}
            # Insert after the currently selected log, or at the end if none is selected.
            insert_pos = self.master_app.selected_log_abs_index + 1 if self.master_app.selected_log_abs_index is not None else len(self.master_app.all_logs)
            self.master_app.all_logs.insert(insert_pos, new_log)
            self.master_app._record_action('add', {'line_num': insert_pos, 'log_entry': new_log})
            self.master_app.update_status("New log entry added.", self.master_app.theme.LOG_LEVEL_COLORS['ADDED'])
        else:
            # --- Modify existing log entry ---
            if self.current_log_index is not None and 0 <= self.current_log_index < len(self.master_app.all_logs):
                line_num = self.current_log_index
                # Record the original state for the undo stack.
                original_log = copy.deepcopy(self.master_app.all_logs[line_num])
                self.master_app.all_logs[line_num].update({'message': formatted_message, 'level': selected_level, 'state': 'MODIFIED'})
                self.master_app._record_action('edit', {'line_num': line_num, 'original_log': original_log})
                self.master_app.update_status(f"Log line {line_num + 1} updated.", self.master_app.theme.LOG_LEVEL_COLORS['MODIFIED'])
            else:
                self.master_app.update_status("Error: Log to edit no longer exists.", self.master_app.theme.LOG_LEVEL_COLORS['DELETED'])
        
        self.master_app.filter_logs(scroll_to_end=False) # Refresh the main display
        self.close_window()

    def _show_log_level_picker(self, event):
        """
        Displays a pop-up listbox to choose a log level.
        
        Args:
            event: The mouse click event that triggered the picker.
        """
        widget = event.widget.master if not isinstance(event.widget, tk.Frame) else event.widget
        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True) # Frameless window
        # Position the popup just below the picker widget
        x, y = widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height()
        
        listbox = tk.Listbox(popup, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, selectbackground=self.theme.ACCENT_COLOR, 
                             selectforeground=self.theme.BG_COLOR, highlightthickness=0, relief="solid", bd=1, font=(self.theme.FONT_FAMILY_UI, 10))
        log_types = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "COMMENT"]
        for level in log_types:
            listbox.insert(tk.END, level)
        listbox.pack(fill="both", expand=True)
        
        # Set the selected level and close the popup when an item is chosen.
        listbox.bind("<<ListboxSelect>>", lambda e: (self.selected_level_var.set(listbox.get(listbox.curselection())), popup.destroy()))
        # Close the popup if it loses focus.
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        
        popup.geometry(f"120x{len(log_types) * 24}+{x}+{y}")
        popup.focus_set()

    def _increase_font_size(self):
        """Increases the font size of the text editor."""
        self.editor_font_size.set(self.editor_font_size.get() + 1)
        self.editor_text.config(font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()))

    def _decrease_font_size(self):
        """Decreases the font size of the text editor to a minimum of 8."""
        if self.editor_font_size.get() > 8:
            self.editor_font_size.set(self.editor_font_size.get() - 1)
            self.editor_text.config(font=(self.theme.FONT_FAMILY_LOG, self.editor_font_size.get()))

    def close_window(self):
        """Destroys the window and resets the instance reference in the main app."""
        self.master_app.editor_window_instance = None
        self.destroy()
