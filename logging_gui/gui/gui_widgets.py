import tkinter as tk

class StyledButton(tk.Button):
    """ 커스텀 스타일과 호버 효과가 적용된 버튼 클래스 """
    def __init__(self, master, parent_frame, **kwargs):
        self.parent_frame = parent_frame
        self.bg_color = kwargs.pop('bg', '#333')
        self.fg_color = kwargs.pop('fg', '#FFF')
        self.hover_color = kwargs.pop('hover_color', '#555')
        self.border_color = kwargs.pop('border_color', '#555')
        self.hover_border_color = kwargs.pop('hover_border_color', '#888')

        super().__init__(master, **kwargs)

        self.config(
            background=self.bg_color,
            foreground=self.fg_color,
            activebackground=self.hover_color,
            activeforeground=self.fg_color,
            relief='flat',
            highlightthickness=1,
            highlightbackground=self.border_color
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        if self['state'] == 'normal':
            self.parent_frame._animate_color(self, self['bg'], self.hover_color)
            self.config(highlightbackground=self.hover_border_color)

    def on_leave(self, event):
        if self['state'] == 'normal':
            self.parent_frame._animate_color(self, self['bg'], self.bg_color)
            self.config(highlightbackground=self.border_color)

    def update_style(self, **kwargs):
        # ... (update_style 메서드 내용은 그대로 유지)
        self.bg_color = kwargs.get('bg', self.bg_color)
        self.fg_color = kwargs.get('fg', self.fg_color)
        self.hover_color = kwargs.get('hover_color', self.hover_color)
        self.border_color = kwargs.get('border_color', self.border_color)
        self.hover_border_color = kwargs.get('hover_border_color', self.hover_border_color)

        self.config(
            background=self.bg_color,
            foreground=self.fg_color,
            activebackground=self.hover_color,
            activeforeground=self.fg_color,
            highlightbackground=self.border_color
        )
        if 'state' in kwargs:
            self.config(state=kwargs['state'])
        if 'text' in kwargs:
            self.config(text=kwargs['text'])
        if 'command' in kwargs:
            self.config(command=kwargs['command'])