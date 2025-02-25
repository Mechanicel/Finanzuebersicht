# classen.py
class Person:
    def __init__(self, name, nachname, freibetrag, banken):
        self.Name = name
        self.Nachname = nachname
        self.Freibetrag = freibetrag  # Dictionary: {Bank: Freibetrag}
        self.Banken = banken        # Liste von Banknamen

    def to_dict(self):
        return {
            "Name": self.Name,
            "Nachname": self.Nachname,
            "Freibetrag": self.Freibetrag,
            "Banken": self.Banken,
        }

class Bank:
    def __init__(self, name, bic):
        self.name = name
        self.bic = bic  # BIC kann auch eine Liste sein

    def to_dict(self):
        return {"Name": self.name, "BIC": self.bic}
