# main.py
import customtkinter
from navigator import Navigator

# Systemeinstellungen
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# Erstelle das Hauptfenster
app = customtkinter.CTk()
app.geometry("720x480")
app.title("Finanzübersicht")

# Initialisiere den Navigator, der die Navigation zwischen Screens übernimmt
navigator = Navigator(app)

# Starte mit dem Hauptmenü
navigator.navigate("main_screen")

def schließenMain():
    app.destroy()

app.protocol("WM_DELETE_WINDOW", schließenMain)
app.mainloop()
