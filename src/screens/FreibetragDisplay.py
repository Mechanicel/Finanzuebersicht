import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)
    freib = state.selected_person.get('Freibetrag', {})
    row = 0
    total = 0.0

    for bank, val in freib.items():
        customtkinter.CTkLabel(app, text=bank).grid(row=row, column=0, padx=20, pady=5)
        customtkinter.CTkLabel(app, text=val).grid(row=row, column=1, padx=20, pady=5)
        try: total += float(val)
        except: pass
        row +=1

    lbl = customtkinter.CTkLabel(app, text=f"Gesamtsumme: {total:.2f}")
    lbl.grid(row=row, column=0, columnspan=2, padx=20, pady=10)
    lbl.configure(fg_color="green" if total<=1000 else "red")
    row+=1

    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonInfo")).grid(row=row, column=0, columnspan=2, padx=20, pady=10)
    zentrieren(app)