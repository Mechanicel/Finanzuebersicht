import customtkinter
from FrontendService.src.helpers.UniversalMethoden import clear_ui, zentrieren
from FrontendService.src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)

    name_var = customtkinter.StringVar()
    bic_var = customtkinter.StringVar()

    def add_bank():
        name = name_var.get().strip()
        bic = bic_var.get().strip()
        if name and bic:
            banks = state.banken
            for bank in banks:
                if bank['Name']==name:
                    if bic not in bank.get('BIC',[]): bank['BIC'].append(bic)
                    break
            else:
                banks.append({'Name':name,'BIC':[bic]})
            state.data_manager.save_bank_data({'Banken':banks})
            state.banken = banks
            entry_name.delete(0,'end'); entry_bic.delete(0,'end')
        else:
            print("Bitte füllen Sie alle Felder aus!")
            if not name: entry_name.configure(fg_color="red")
            if not bic: entry_bic.configure(fg_color="red")

    def reset_bg(_):
        entry_name.configure(fg_color="white")
        entry_bic.configure(fg_color="white")

    customtkinter.CTkLabel(app, text="Name:").grid(row=0,column=0,padx=20,pady=10)
    entry_name = customtkinter.CTkEntry(app, textvariable=name_var)
    entry_name.grid(row=0,column=1,padx=20,pady=10); entry_name.bind("<FocusIn>",reset_bg)

    customtkinter.CTkLabel(app, text="BIC:").grid(row=1,column=0,padx=20,pady=10)
    entry_bic = customtkinter.CTkEntry(app, textvariable=bic_var)
    entry_bic.grid(row=1,column=1,padx=20,pady=10); entry_bic.bind("<FocusIn>",reset_bg)

    customtkinter.CTkButton(app, text="Hinzufügen", command=add_bank).grid(row=2,column=0,columnspan=2,padx=20,pady=10)
    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("MainScreen")).grid(row=3,column=0,columnspan=2,padx=20,pady=10)

    zentrieren(app)