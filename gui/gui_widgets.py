
import tkinter as tk

class StyledButton(tk.Button):
    """
    # A custom button class with enhanced styling and hover effects.
    # 향상된 스타일과 호버 효과를 가진 커스텀 버튼 클래스입니다.
    """
    def __init__(self, master, parent_frame, **kwargs):
        """
        # Initializes the StyledButton.
        # StyledButton을 초기화합니다.

        # Args:
        #     master: The parent widget.
        #             (부모 위젯)
        #     parent_frame: The main application frame, used for color animations.
        #                   (색상 애니메이션에 사용될 메인 애플리케이션 프레임)
        #     **kwargs: Standard tk.Button arguments and custom style arguments.
        #               (표준 tk.Button 인수 및 사용자 정의 스타일 인수)
        """
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
        """
        # Handles the mouse enter event to apply hover effects.
        # 마우스 진입 이벤트를 처리하여 호버 효과를 적용합니다.
        """
        if self['state'] == 'normal':
            self.parent_frame._animate_color(self, self['bg'], self.hover_color)
            self.config(highlightbackground=self.hover_border_color)

    def on_leave(self, event):
        """
        # Handles the mouse leave event to remove hover effects.
        # 마우스 이탈 이벤트를 처리하여 호버 효과를 제거합니다.
        """
        if self['state'] == 'normal':
            self.parent_frame._animate_color(self, self['bg'], self.bg_color)
            self.config(highlightbackground=self.border_color)

    def update_style(self, **kwargs):
        """
        # Updates the button's style dynamically.
        # 버튼의 스타일을 동적으로 업데이트합니다.
        """
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
