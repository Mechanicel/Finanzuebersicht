class Account:
    def __init__(self, kontotyp, bank, bic=None, blz=None, account_number=None, deposit_number=None, extra=None,
                 kontostaende=None):
        """
        Allgemeine Konto-Klasse.
        :param kontotyp: Der Typ des Kontos (z.B. "Girokonto", "Festgeldkonto", etc.)
        :param bank: Name der Bank.
        :param bic: BIC der Bank.
        :param blz: Bankleitzahl.
        :param account_number: Kontonummer (falls vorhanden).
        :param deposit_number: Deponummer (falls vorhanden).
        :param extra: Dictionary mit weiteren Feldern (z.B. Laufzeit, Zinssatz, Anlagedatum, etc.)
        :param kontostaende: Liste von Kontostand-Einträgen im Format "YYYY-MM-DD: Wert"
        """
        self.kontotyp = kontotyp
        self.bank = bank
        self.bic = bic
        self.blz = blz
        self.account_number = account_number
        self.deposit_number = deposit_number
        self.extra = extra if extra is not None else {}
        self.kontostaende = kontostaende if kontostaende is not None else []

    def to_dict(self):
        data = {
            "Kontotyp": self.kontotyp,
            "Bank": self.bank,
            "BIC": self.bic,
            "BLZ": self.blz,
            "Kontostaende": self.kontostaende,
        }
        if self.account_number:
            data["Kontonummer"] = self.account_number
        if self.deposit_number:
            data["Deponummer"] = self.deposit_number
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data):
        kontotyp = data.get("Kontotyp", "")
        bank = data.get("Bank", "")
        bic = data.get("BIC", None)
        blz = data.get("BLZ", None)
        account_number = data.get("Kontonummer", None)
        deposit_number = data.get("Deponummer", None)
        kontostaende = data.get("Kontostaende", [])

        # Extrahiere alle weiteren Felder, die nicht standardmäßig zugeordnet sind
        reserved_keys = {"Kontotyp", "Bank", "BIC", "BLZ", "Kontonummer", "Deponummer", "Kontostaende"}
        extra = {k: v for k, v in data.items() if k not in reserved_keys}

        return cls(kontotyp, bank, bic, blz, account_number, deposit_number, extra, kontostaende)
