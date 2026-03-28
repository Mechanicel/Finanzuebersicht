from __future__ import annotations

import customtkinter as ctk


class SimpleTooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self._show, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None):
        if self.tip_window is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip_window = ctk.CTkToplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(
            self.tip_window,
            text=self.text,
            justify="left",
            wraplength=320,
            fg_color="#1f1f1f",
            corner_radius=8,
            padx=8,
            pady=6,
        )
        label.pack()

    def _hide(self, _event=None):
        if self.tip_window is not None:
            self.tip_window.destroy()
            self.tip_window = None


def attach_tooltip(widget, text: str):
    return SimpleTooltip(widget, text)


def info_label(parent, text: str, tooltip: str):
    label = ctk.CTkLabel(parent, text=f"{text}  ⓘ", text_color="gray75")
    attach_tooltip(label, tooltip)
    return label
