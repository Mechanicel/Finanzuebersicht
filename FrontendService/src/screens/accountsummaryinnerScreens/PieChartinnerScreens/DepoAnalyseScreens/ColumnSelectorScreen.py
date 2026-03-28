from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk


class ColumnSelector:
    def __init__(self, parent, columns: list[str], on_change: Callable[[list[str]], None] | None = None):
        self._on_change = on_change
        self._vars: dict[str, ctk.BooleanVar] = {}
        self._checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")

        for col in columns:
            var = ctk.BooleanVar(value=True)
            self._vars[col] = var
            chk = ctk.CTkCheckBox(
                self.frame,
                text=col,
                variable=var,
                command=self._emit,
            )
            chk.pack(side="left", padx=5, pady=5)
            self._checkboxes[col] = chk

    def _emit(self):
        if self._on_change:
            self._on_change(self.selected_columns())

    def selected_columns(self) -> list[str]:
        return [name for name, var in self._vars.items() if bool(var.get())]

    def checkboxes(self) -> dict[str, ctk.CTkCheckBox]:
        return self._checkboxes


def create_column_selector_screen(parent, columns, callback=None):
    selector = ColumnSelector(parent, list(columns), callback)
    selector.frame.pack(side="left", padx=2, pady=2)
    return selector
