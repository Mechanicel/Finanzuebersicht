import customtkinter
from src.helpers.UniversalMethoden import clear_ui, zentrieren
from src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, selected_index:int=0, **kwargs):
    clear_ui(app)
    person = state.selected_person
    konten = person.get('Konten', [])
    if not konten: return navigator.navigate("PersonInfo")
    idx = max(0, min(selected_index, len(konten)-1))
    account = konten[idx]

    customtkinter.CTkLabel(app, text=f"Konten bearbeiten – {person['Name']} {person['Nachname']}").grid(row=0,column=0,columnspan=4,padx=20,pady=10,sticky="w")
    choices = [f"{i}: {k['Kontotyp']}" for i,k in enumerate(konten)]
    var = customtkinter.StringVar(value=choices[idx])
    customtkinter.CTkComboBox(app, values=choices, variable=var, state="readonly", command=lambda v: navigator.navigate("AccountEditing", selected_index=int(v.split(":")[0]))).grid(row=1,column=0,columnspan=4,padx=20,pady=5,sticky="we")

    frame = customtkinter.CTkFrame(app)
    frame.grid(row=2,column=0,columnspan=4,padx=20,pady=10,sticky="nsew")
    zentrieren(frame)

    # Felder statisch, dann dynamisch wie vorher, aber haben Zugriff auf person und konten
    # Speicher und Löschen:
    def save():
        state.save_person(person)
        navigator.navigate("PersonInfo")
    def delete():
        konten.pop(idx)
        state.save_person(person)
        navigator.navigate("PersonInfo")

    customtkinter.CTkButton(frame, text="Speichern", command=save).grid(row=0,column=0,padx=5,pady=5)
    customtkinter.CTkButton(frame, text="Löschen", command=delete).grid(row=0,column=1,padx=5,pady=5)
    customtkinter.CTkButton(app, text="Zurück", command=lambda: navigator.navigate("PersonInfo")).grid(row=3,column=0,columnspan=4,pady=10)
    zentrieren(app)