class Person:
    def __init__(self, name, nachname, freibetrag=None, banken=None, konten=None):
        self.name = name
        self.nachname = nachname
        self.freibetrag = freibetrag if freibetrag is not None else {}
        self.banken = banken if banken is not None else []
        self.konten = konten if konten is not None else []

    def to_dict(self):
        return {
            "Name": self.name,
            "Nachname": self.nachname,
            "Freibetrag": self.freibetrag,
            "Banken": self.banken,
            "Konten": self.konten,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("Name", ""),
            nachname=data.get("Nachname", ""),
            freibetrag=data.get("Freibetrag", {}),
            banken=data.get("Banken", []),
            konten=data.get("Konten", []),
        )

