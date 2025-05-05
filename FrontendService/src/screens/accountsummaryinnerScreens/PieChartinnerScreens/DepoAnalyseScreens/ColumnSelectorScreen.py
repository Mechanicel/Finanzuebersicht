import customtkinter as ctk

def create_column_selector_screen(parent, columns, callback):
    """
    Erzeugt Checkboxen für jede Kennzahl, um Linien im Chart
    ein- oder auszublenden. Ruft callback(column, state) auf.
    """
    for col in columns:
        chk = ctk.CTkCheckBox(
            parent,
            text=col,
            command=lambda c=col: callback(c, None)
        )
        chk.select()  # standardmäßig alle sichtbar
        chk.pack(side="left", padx=5, pady=5)
