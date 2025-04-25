import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

def create_column_selector_screen(parent, columns: list, on_change):
    """
    Erstellt einen scrollbaren Column-Selector mit alphabetisch sortierten Checkboxes.
    """
    logger.debug("Erstelle ColumnSelector für Spalten (unsortiert): %s", columns)
    # Container-Rahmen
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", side="right", padx=10, pady=10)

    # Überschrift
    ctk.CTkLabel(
        container,
        text="Spalten anzeigen",
        font=("Arial", 12, "bold")
    ).pack(pady=(0,5))

    # Scrollbarer Bereich für die Checkboxes
    scroll_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", width=200, height=400)
    scroll_frame.pack(fill="both", expand=True)

    # Sortieren der Spaltenliste
    sorted_cols = sorted(columns, key=lambda s: s.lower())
    logger.debug("Spalten alphabetisch sortiert: %s", sorted_cols)

    # Anlegen der Checkboxes
    for col in sorted_cols:
        var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(
            scroll_frame,
            text=col,
            variable=var,
            command=lambda c=col, v=var: on_change(c, v.get())
        )
        chk.pack(anchor="w", pady=2)
