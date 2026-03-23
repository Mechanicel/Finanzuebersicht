import customtkinter as ctk

from src.helpers.UniversalMethoden import clear_ui

PAD_X = 24
PAD_Y = 16
CARD_PAD = 14
BUTTON_HEIGHT = 38

STATUS_COLORS = {
    "info": ("#2F5D8A", "#294763"),
    "success": ("#2E7D32", "#205A24"),
    "warning": ("#A97C00", "#7A5900"),
    "error": ("#B00020", "#850018"),
}


def create_page(app, title: str, subtitle: str = "", back_command=None, scrollable: bool = False):
    clear_ui(app)
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)

    frame_cls = ctk.CTkScrollableFrame if scrollable else ctk.CTkFrame
    root = frame_cls(app, corner_radius=12)
    root.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
    root.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(root, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(PAD_Y, 10))
    header.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(header, text=title, font=("Arial", 28, "bold")).grid(row=0, column=0, sticky="w")
    if subtitle:
        ctk.CTkLabel(header, text=subtitle, text_color="gray70", font=("Arial", 14)).grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )

    if back_command:
        ctk.CTkButton(
            header,
            text="← Zurück",
            width=110,
            height=34,
            fg_color="gray35",
            hover_color="gray25",
            command=back_command,
        ).grid(row=0, column=1, rowspan=2, sticky="e")

    status = ctk.CTkLabel(
        root,
        text="",
        corner_radius=8,
        padx=10,
        pady=8,
        anchor="w",
        fg_color="transparent",
        text_color="gray90",
    )
    status.grid(row=1, column=0, sticky="ew", padx=PAD_X)
    status.grid_remove()

    content = ctk.CTkFrame(root, fg_color="transparent")
    content.grid(row=2, column=0, sticky="nsew", padx=PAD_X, pady=(12, PAD_Y))
    content.grid_columnconfigure(0, weight=1)

    return {"root": root, "header": header, "status": status, "content": content}


def set_status(status_label, message: str, kind: str = "info"):
    if not message:
        status_label.grid_remove()
        return
    fg, hover = STATUS_COLORS.get(kind, STATUS_COLORS["info"])
    status_label.configure(text=message, fg_color=fg, text_color="white")
    status_label.grid()
    status_label.lift()
    status_label._hover_color = hover


def section_card(parent, title: str, subtitle: str = ""):
    card = ctk.CTkFrame(parent, corner_radius=12)
    card.pack(fill="x", pady=(0, 14))
    card.grid_columnconfigure(0, weight=1)
    if title:
        ctk.CTkLabel(card, text=title, font=("Arial", 18, "bold")).grid(
            row=0, column=0, sticky="w", padx=CARD_PAD, pady=(CARD_PAD, 0)
        )
    if subtitle:
        ctk.CTkLabel(card, text=subtitle, text_color="gray70", font=("Arial", 12)).grid(
            row=1, column=0, sticky="w", padx=CARD_PAD, pady=(2, 10)
        )
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=2, column=0, sticky="ew", padx=CARD_PAD, pady=(2, CARD_PAD))
    body.grid_columnconfigure(0, weight=1)
    return card, body


def action_bar(parent):
    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(fill="x", pady=(8, 0))
    bar.grid_columnconfigure((0, 1, 2), weight=1)
    return bar


def primary_button(parent, text: str, command, column: int = 0):
    btn = ctk.CTkButton(parent, text=text, height=BUTTON_HEIGHT, command=command)
    btn.grid(row=0, column=column, padx=6, pady=6, sticky="ew")
    return btn


def secondary_button(parent, text: str, command, column: int = 1):
    btn = ctk.CTkButton(parent, text=text, height=BUTTON_HEIGHT, fg_color="gray35", hover_color="gray25", command=command)
    btn.grid(row=0, column=column, padx=6, pady=6, sticky="ew")
    return btn


def danger_button(parent, text: str, command, column: int = 2):
    btn = ctk.CTkButton(parent, text=text, height=BUTTON_HEIGHT, fg_color="#A61B1B", hover_color="#7A1010", command=command)
    btn.grid(row=0, column=column, padx=6, pady=6, sticky="ew")
    return btn


def stats_row(parent, stats: list[tuple[str, str]]):
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=(0, 14))
    for i, (label, value) in enumerate(stats):
        card = ctk.CTkFrame(row, corner_radius=10)
        card.grid(row=0, column=i, padx=6, sticky="ew")
        row.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(card, text=label, text_color="gray70", font=("Arial", 11)).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(card, text=value, font=("Arial", 20, "bold")).pack(anchor="w", padx=10, pady=(0, 8))
    return row


def empty_state(parent, message: str):
    box = ctk.CTkFrame(parent, corner_radius=10)
    box.pack(fill="x", pady=10)
    ctk.CTkLabel(box, text=message, text_color="gray70", font=("Arial", 14)).pack(padx=16, pady=16)
    return box
