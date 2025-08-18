# src/gui/log_display.py

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

from .theme import Theme
from .config import PAUSE_FLAG_PATH, LOG_DIR
from .editor_window import EditorWindow



class LogDisplay(tk.Frame):
    def __init__(self, master=None):
        self.theme = Theme()
        super().__init__(master, bg=self.theme.BG_COLOR)
        self.master = master
        self.master.title("GLEN Real-Time Log")
        self.master.geometry("1200x800")
        self.master.configure(bg=self.theme.BG_COLOR)
        empty_menu = Menu(self.master); self.master.config(menu=empty_menu)
        self.pack(fill="both", expand=True)
        
        self.all_logs = []; self.undo_stack = []; self.redo_stack = []
        self.log_filter_vars = {}
        self.log_filter_vars['SYSTEM'] = BooleanVar(value=True) # SYSTEM 로그는 항상 표시

        self.autocomplete_commands = {'/add': ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL"]}
        self.autocomplete_popup = None
        self.log_queue = queue.Queue()
        self.last_progress_message = None

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
        self.master.bind_all("<Control-z>", lambda e: self._undo(1))
        self.master.bind_all("<Control-y>", lambda e: self._redo(1))

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
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        style = ttk.Style(); style.theme_use('clam')
        style.configure("Custom.Vertical.TScrollbar", gripcount=0, background="#555555", darkcolor=self.theme.WIDGET_BG_COLOR, lightcolor=self.theme.WIDGET_BG_COLOR, troughcolor=self.theme.BG_COLOR, bordercolor=self.theme.BG_COLOR, relief="flat", arrowsize=0)
        style.map("Custom.Vertical.TScrollbar", background=[('active', self.theme.ACCENT_COLOR), ('!disabled', '#555555')], relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        top_frame = Frame(self, bg=self.theme.BG_COLOR); top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        button_frame = Frame(top_frame, bg=self.theme.BG_COLOR); button_frame.pack(side="left", padx=(0, 20))
        
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

        filter_frame = tk.LabelFrame(top_frame, text="Log Filters", bg=self.theme.BG_COLOR, fg=self.theme.TEXT_COLOR, font=(self.theme.FONT_FAMILY_UI, 10, "bold"), padx=10, pady=5, bd=1, relief="solid")
        filter_frame.pack(side="left", fill="x", expand=True)
        
        log_types_ordered = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "COMMENT"]
        for log_type in log_types_ordered:
            if log_type not in self.theme.LOG_LEVEL_COLORS: continue
            var = BooleanVar(value=True)
            chk_color = self.theme.LOG_LEVEL_COLORS.get(log_type, self.theme.TEXT_COLOR)
            chk = Checkbutton(filter_frame, text=log_type, variable=var, command=self.filter_logs, bg=self.theme.BG_COLOR, fg=chk_color, selectcolor=self.theme.WIDGET_BG_COLOR, font=(self.theme.FONT_FAMILY_UI, 9), bd=0, highlightthickness=0, activebackground=self.theme.BG_COLOR, activeforeground=chk_color, cursor="hand2")
            chk.pack(side="left", padx=5)
            self.log_filter_vars[log_type] = var
            
        font_control_frame = Frame(top_frame, bg=self.theme.BG_COLOR); font_control_frame.pack(side="right", padx=10)
        font_plus_button = Button(font_control_frame, text="A+", command=self._increase_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5)
        font_plus_button.pack(side="right", padx=(2,0))
        font_minus_button = Button(font_control_frame, text="A-", command=self._decrease_font_size, bg=self.theme.WIDGET_BG_COLOR, fg=self.theme.TEXT_COLOR, relief="flat", padx=5)
        font_minus_button.pack(side="right")

        log_area_frame = Frame(self, bg=self.theme.BG_COLOR)
        log_area_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        text_sub_frame = Frame(log_area_frame, bg="#121212")
        text_sub_frame.pack(side="top", fill="both", expand=True)
        text_sub_frame.grid_rowconfigure(0, weight=1)
        text_sub_frame.grid_columnconfigure(0, weight=1)

        self.log_area = tk.Text(text_sub_frame, wrap=tk.WORD, state='disabled', font=(self.theme.FONT_FAMILY_LOG, self.log_font_size), bg="#121212", fg=self.theme.TEXT_COLOR, insertbackground="white", bd=0, highlightthickness=0, padx=5, pady=5)
        self.log_area.grid(row=0, column=0, sticky="nsew")
        self.log_area.bind("<Button-1>", self._on_log_area_click)

        self.vsb = ttk.Scrollbar(text_sub_frame, orient="vertical", command=self.log_area.yview, style="Custom.Vertical.TScrollbar")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.log_area.config(yscrollcommand=self.vsb.set)
        
        self.progress_label = Label(log_area_frame, text="", font=(self.theme.FONT_FAMILY_LOG, self.log_font_size), bg="#121212", fg=self.theme.LOG_LEVEL_COLORS['PROGRESS'], anchor="w", padx=5)
        self.progress_label.pack(side="bottom", fill="x")

        bottom_frame = Frame(self, bg=self.theme.BG_COLOR)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        comment_container_frame = Frame(bottom_frame, bg=self.theme.ENTRY_BG_COLOR)
        comment_container_frame.grid(row=0, column=0, sticky="ew")
        comment_container_frame.grid_columnconfigure(1, weight=1)
        self.command_button = Button(comment_container_frame, text="/", command=self._show_command_dropdown, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 12), relief="flat", activebackground=self.theme.ENTRY_BG_COLOR, activeforeground="white", bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.command_button.grid(row=0, column=0, sticky="nsew")
        self.command_button.bind("<Enter>", lambda e: self.command_button.config(fg="white"))
        self.command_button.bind("<Leave>", lambda e: self.command_button.config(fg=self.theme.ACCENT_COLOR) if self.command_button['state'] == 'normal' else None)
        self.comment_entry = tk.Text(comment_container_frame, font=(self.theme.FONT_FAMILY_UI, 11), bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR, insertbackground="white", relief="flat", bd=0, highlightthickness=0, height=1, wrap="none", padx=10, pady=8)
        self.comment_entry.grid(row=0, column=1, sticky="ew")
        self.comment_entry.bind("<Return>", self.send_comment); self.comment_entry.bind("<Shift-Return>", "break")
        self.comment_entry.bind("<FocusIn>", self._on_comment_entry_focus_in); self.comment_entry.bind("<FocusOut>", self._on_comment_entry_focus_out)
        self.comment_entry.bind("<Key>", self._on_comment_entry_key_press); self.comment_entry.bind("<KeyRelease>", self._handle_autocomplete)
        self.send_button = Button(comment_container_frame, text="➤", command=self.send_comment, bg=self.theme.ENTRY_BG_COLOR, fg=self.theme.ACCENT_COLOR, font=(self.theme.FONT_FAMILY_UI, 14, "bold"), relief="flat", activebackground=self.theme.ENTRY_BG_COLOR, activeforeground="white", bd=0, highlightthickness=0, cursor="hand2", width=3, height=1)
        self.send_button.grid(row=0, column=2, sticky="nsew")
        self.send_button.bind("<Enter>", lambda e: self.send_button.config(fg="white"))
        self.send_button.bind("<Leave>", lambda e: self.send_button.config(fg=self.theme.ACCENT_COLOR) if self.send_button['state'] == 'normal' else None)
        status_frame = Frame(bottom_frame, bg=self.theme.BG_COLOR); status_frame.grid(row=1, column=0, sticky="e", padx=5, pady=(5,0))
        self.status_canvas = Canvas(status_frame, width=10, height=10, bg=self.theme.BG_COLOR, highlightthickness=0); self.status_canvas.pack(side="left", pady=2)
        self.status_label = Label(status_frame, text="Idle", font=(self.theme.FONT_FAMILY_UI, 9), bg=self.theme.BG_COLOR, fg=self.theme.DISABLED_TEXT_COLOR); self.status_label.pack(side="left", padx=(5,0))
        self.log_area.tag_bind("FILE_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("FILE_LINK", "<Leave>", self._on_link_leave)
        self.log_area.tag_bind("FILE_LINK", "<Control-Button-1>", self._on_link_click); self.log_area.tag_bind("FILE_LINK", "<Shift-Button-1>", self._on_link_shift_click)
        self.log_area.tag_bind("WEB_LINK", "<Enter>", self._on_link_enter); self.log_area.tag_bind("WEB_LINK", "<Leave>", self._on_link_leave)
        self.log_area.tag_bind("WEB_LINK", "<Control-Button-1>", self._on_link_click)
        self.update_ui_for_state()

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
        if self.editor_window_instance and self.editor_window_instance.winfo_exists(): self.editor_window_instance.lift(); self.editor_window_instance.focus_set(); return
        self.editor_window_instance = EditorWindow(self, self.selected_log_abs_index)

    def _on_log_area_click(self, event):
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
        self.filter_logs(scroll_to_end=scroll_to_end)

    def configure_tags(self):
        base_font = (self.theme.FONT_FAMILY_LOG, self.log_font_size)
        self.log_area.config(font=base_font)
        
        for level, color in self.theme.LOG_LEVEL_COLORS.items():
            font_config = list(base_font)
            extra_config = {}
            if level == "FATAL": font_config.extend(["bold"])
            elif level in ["COMMENT", "ADDED", "MODIFIED", "SYSTEM"]: font_config.extend(["italic"])
            elif level == "DELETED": extra_config["overstrike"] = True
            
            self.log_area.tag_config(level, foreground=color, font=tuple(font_config), **extra_config)
        
        self.log_area.tag_config("highlight", background="#5D5D9A", foreground="#FFFFFF")
        self.log_area.tag_config("FILE_LINK", foreground=self.theme.LINK_COLOR, underline=True)
        self.log_area.tag_config("WEB_LINK", foreground=self.theme.LINK_COLOR, underline=True)


    def _get_tags_for_log(self, log_entry):
        tags = [log_entry.get('level', 'INFO')]
        if 'state' in log_entry and log_entry['state'] != 'SAVED': tags.append(log_entry['state'])
        return tuple(tags)

    def _apply_link_tags(self, start_index, end_index=None):
        if end_index is None: end_index = f"{start_index.split('.')[0]}.end"
        line_text = self.log_area.get(start_index, end_index)
        path_regex = r'(["\']?)(@(?:[a-zA-Z]:(?:[\\/][^@\n\r<>"\']*)?))(["\']?)'
        for match in re.finditer(path_regex, line_text):
            path_text = match.group(2)
            offset = match.group(0).find(path_text)
            tag_start = f"{start_index}+{match.start() + offset}c"
            tag_end = f"{tag_start}+{len(path_text)}c"
            self.log_area.tag_add("FILE_LINK", tag_start, tag_end)
        for match in re.finditer(r'https?://[^\s<>"\'"]+', line_text):
            tag_start = f"{start_index}+{match.start()}c"
            tag_end = f"{start_index}+{match.end()}c"
            self.log_area.tag_add("WEB_LINK", tag_start, tag_end)

    def add_log(self, message, level='INFO', to_file=True, scroll=True):
        log_entry = {'message': message, 'level': level, 'state': 'SAVED'}
        self.all_logs.append(log_entry)
        if self.log_filter_vars.get(level, BooleanVar(value=True)).get():
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

    def filter_logs(self, scroll_to_end=False):
        current_scroll_fraction = self.log_area.yview()[0] 
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        for i, log_entry in enumerate(self.all_logs):
            tags = list(self._get_tags_for_log(log_entry)) + [f"log_index_{i}"]
            if log_entry.get('state') == 'DELETED' or self.log_filter_vars.get(log_entry.get('level'), BooleanVar(value=True)).get():
                self.log_area.insert(tk.END, log_entry['message'] + '\n', tuple(tags))
                self._apply_link_tags(self.log_area.index(f"{tk.END}-2l"))
        self.log_area.configure(state='disabled')
        if scroll_to_end: self.log_area.yview_moveto(1.0)
        else: self.log_area.yview_moveto(current_scroll_fraction)

    def send_comment(self, event=None):
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
            from .config import THINK_CORE_SCRIPT_PATH
            script_path = THINK_CORE_SCRIPT_PATH

            if not os.path.exists(script_path):
                self.update_status(f"Error: Script not found at {script_path}", self.theme.LOG_LEVEL_COLORS['DELETED'])
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
            self.update_status(f"Starting script: {os.path.basename(script_path)}", self.theme.ACCENT_COLOR)
            self.master.update_idletasks()

            self.last_progress_message = None
            self.update_progress_display("")

            log_dir = LOG_DIR
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"glen_log_{timestamp}.log"
            self.current_log_file_path = os.path.join(log_dir, log_filename)
            try: self.log_file = open(self.current_log_file_path, "a", encoding="utf-8", buffering=1)
            except IOError as e: self.update_status(f"Error opening log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED']); return

            python_executable = sys.executable
            try:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                
                self.think_core_process = subprocess.Popen(
                    [python_executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding='utf-8', errors='replace', bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                    cwd=project_root
                )
                self.is_running = True
                self.log_file_open = True
                self.log_queue.put(('add', {'message': "GLEN Think Core started.", 'level': 'INFO'}))
                threading.Thread(target=self._read_think_core_output, daemon=True).start()
                self.master.after(50, self.process_log_queue)
            except Exception as e: self.update_status(f"Error starting GLEN Think Core: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        
        self.update_ui_for_state()

    def process_log_queue(self):
        messages_processed = False
        try:
            while True:
                action, data = self.log_queue.get_nowait()
                messages_processed = True
                
                level = data.get('level', '').upper()
                msg_text = data.get('message', '')

                if level == 'PROGRESS':
                    self.update_progress_display(msg_text.replace('\r', '').strip())
                    self.last_progress_message = data
                    continue

                if self.last_progress_message:
                    is_resume_or_pause_message = bool(re.search(r'\b(resumed|paused)\b', msg_text, re.I))
                    if not self.is_paused and not is_resume_or_pause_message:
                        final_data = dict(self.last_progress_message)
                        final_data['level'] = 'INFO'
                        final_message = final_data['message'].replace('\r', '').strip()
                        self.add_log(final_message, final_data.get('level', 'INFO'), scroll=False)
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

        self.undo_stack.clear()
        self.redo_stack.clear()
        self.update_ui_for_state()
        self.filter_logs(scroll_to_end=False)
        self.update_status("Think Core process finished.", self.theme.ACCENT_COLOR)

    def _read_think_core_output(self):
        def enqueue_output(stream):
            for line in iter(stream.readline, ''):
                line_stripped = line.strip()
                if not line_stripped: continue
                
                level_match = re.search(r"TRACE|DEBUG|INFO|WARNING|ERROR|FATAL|COMMENT|PROGRESS|TIMER", line_stripped)
                level = level_match.group(0).strip('[]') if level_match else "INFO"
                
                self.log_queue.put(('add', {'message': line_stripped, 'level': level}))
            stream.close()

        stdout_thread = threading.Thread(target=enqueue_output, args=(self.think_core_process.stdout,), daemon=True)
        stderr_thread = threading.Thread(target=enqueue_output, args=(self.think_core_process.stderr,), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        self.think_core_process.wait()
        self.master.after(0, self._on_run_finish)


    def toggle_pause_resume(self):
        if self.is_paused:
            if self.undo_stack: self.save_log_changes()
            if os.path.exists(PAUSE_FLAG_PATH): os.remove(PAUSE_FLAG_PATH)
            self.is_paused = False
            self.log_queue.put(('add', {'message': "GLEN Think Core resumed.", 'level': 'INFO'}))
        else:
            if not self.is_running: return
            with open(PAUSE_FLAG_PATH, "w") as f: f.write("paused")
            self.is_paused = True
            self.filter_logs(scroll_to_end=False)
            self.log_queue.put(('add', {'message': "GLEN Think Core paused.", 'level': 'INFO'}))
        self.update_ui_for_state()

    def open_log_folder(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        try: os.startfile(log_dir); self.update_status(f"Opened log folder: {log_dir}", self.theme.ACCENT_COLOR)
        except Exception as e: self.update_status(f"Error opening folder: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])

    def open_log_file(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
        if not os.path.isdir(log_dir):
            self.update_status(f"Error: Log directory not found: {log_dir}", self.theme.LOG_LEVEL_COLORS['DELETED']); return
        
        file_path = filedialog.askopenfilename(initialdir=log_dir, title="Select Log File", filetypes=(("Log files", "*.log"), ("all files", "*.*")))
        if not file_path: return

        try:
            self.all_logs, self.undo_stack, self.redo_stack = [], [], []
            log_pattern = re.compile(r"\[(TRACE|DEBUG|INFO|PROGRESS|WARNING|ERROR|FATAL|COMMENT)\]")

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            processed_lines = []
            for i, line in enumerate(lines):
                is_progress = "[PROGRESS]" in line
                
                if is_progress:
                    is_last_line = (i == len(lines) - 1)
                    next_line_is_not_progress = False
                    if not is_last_line and "[PROGRESS]" not in lines[i+1]: next_line_is_not_progress = True
                    
                    if is_last_line or next_line_is_not_progress:
                        processed_lines.append(line)
                else: processed_lines.append(line)

            for line in processed_lines:
                line_stripped = line.strip()
                if not line_stripped: continue
                
                match = log_pattern.search(line_stripped)
                level = match.group(1).upper() if match else "INFO"
                self.all_logs.append({'message': line_stripped, 'level': level, 'state': 'SAVED'})

            self.log_file_open, self.is_running = True, False
            self.current_log_file_path = file_path
            self.filter_logs(scroll_to_end=True)
            self.update_status(f"Opened log file: {os.path.basename(file_path)}", self.theme.ACCENT_COLOR)
        except Exception as e:
            self.update_status(f"Error reading log file: {e}", self.theme.LOG_LEVEL_COLORS['DELETED'])
        
        self.update_ui_for_state()

    def _increase_font_size(self):
        self.log_font_size += 1; self.configure_tags(); self.filter_logs(scroll_to_end=False)
        self.update_status(f"Font size: {self.log_font_size}", self.theme.ACCENT_COLOR)

    def _decrease_font_size(self):
        if self.log_font_size > 8: self.log_font_size -= 1; self.configure_tags(); self.filter_logs(scroll_to_end=False)
        else: self.update_status("Minimum font size reached.", self.theme.DISABLED_TEXT_COLOR)

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
        if self.is_running:
            self.run_exit_button.config(text="Kill", bg=self.theme.KILL_COLOR, command=self.toggle_run_exit, state="normal")
            self._bind_button_effects(self.run_exit_button, self.theme.KILL_COLOR, self.theme.KILL_HOVER_COLOR)
            if self.is_paused:
                if self.undo_stack:
                    self.pause_resume_button.config(text="Save", bg=self.theme.LOG_LEVEL_COLORS['MODIFIED'], command=self.save_log_changes, state="normal", fg="white")
                    self._bind_button_effects(self.pause_resume_button, self.theme.LOG_LEVEL_COLORS['MODIFIED'], self.theme.PRIMARY_HOVER_COLOR)
                else:
                    self.pause_resume_button.config(text="Resume", bg=self.theme.LOG_LEVEL_COLORS['ADDED'], command=self.toggle_pause_resume, state="normal", fg="white")
                    self._bind_button_effects(self.pause_resume_button, self.theme.LOG_LEVEL_COLORS['ADDED'], self.theme.SUCCESS_HOVER_COLOR)
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
                self.pause_resume_button.config(bg=self.theme.LOG_LEVEL_COLORS['MODIFIED'], fg="white")
                self._bind_button_effects(self.pause_resume_button, self.theme.LOG_LEVEL_COLORS['MODIFIED'], self.theme.PRIMARY_HOVER_COLOR)
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
        button.original_bg, button.hover_bg = default_bg, hover_bg
        def on_enter(event): 
            if button['state'] == 'normal': self._animate_color(button, button['bg'], button.hover_bg)
        def on_leave(event):
            if button['state'] == 'normal': self._animate_color(button, button['bg'], button.original_bg)
        button.bind("<Enter>", on_enter, add="+ "); button.bind("<Leave>", on_leave, add="+ ")