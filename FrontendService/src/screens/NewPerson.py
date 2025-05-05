import customtkinter
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)

    name_var = customtkinter.StringVar()
    nach_var = customtkinter.StringVar()

    def proceed():
        n = name_var.get().strip()
        nn = nach_var.get().strip()
        if not n or not nn:
            if not n: entry_name.configure(fg_color="lightcoral")
            if not nn: entry_nach.configure(fg_color="lightcoral")
            return
        # Existenz prüfen
        for p in state.personen:
            if p['Name']==n and p['Nachname']==nn:
                print("Diese Person existiert bereits.")
                return
        new = {'Name':n,'Nachname':nn,'Freibetrag':{},'Banken':[], 'Konten':[]}
        state.personen.append(new)
        state.data_manager.save_personen(state.personen)
        navigator.navigate("MainScreen")

    def reset_bg(_):
        entry_name.configure(fg_color="white")
        entry_nach.configure(fg_color="white")

    customtkinter.CTkLabel(app, text="Name:").grid(row=0,column=0,padx=20,pady=10)
    entry_name = customtkinter.CTkEntry(app, textvariable=name_var)
    entry_name.grid(row=0,column=1,padx=20,pady=10)
    entry_name.bind("<FocusIn>", reset_bg)

    customtkinter.CTkLabel(app, text="Nachname:").grid(row=1,column=0,padx=20,pady=10)
    entry_nach = customtkinter.CTkEntry(app, textvariable=nach_var)
    entry_nach.grid(row=1,column=1,padx=20,pady=10)
    entry_nach.bind("<FocusIn>", reset_bg)

    customtkinter.CTkButton(app, text="Fortfahren", command=proceed).grid(row=2, column=0, columnspan=2, padx=20,pady=10)
    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("MainScreen")).grid(row=3,column=0,columnspan=2,padx=20,pady=10)

    zentrieren(app)