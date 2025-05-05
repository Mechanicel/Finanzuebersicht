class Bank:
    def __init__(self, name, bic):
        self.name = name
        # BIC kann entweder ein String oder eine Liste sein
        if isinstance(bic, list):
            self.bic = bic
        else:
            self.bic = [bic]

    def to_dict(self):
        return {
            "Name": self.name,
            "BIC": self.bic,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("Name", ""),
            bic=data.get("BIC", [])
        )

