from utils import append_dict_to_csv, get_last_row_id, get_with_id

BUILDING_CSV = "data/Building.csv"


class Building:
    serialization = {}
    deserialization = {
        "id": int,
        "floor": int,
        "apartment": lambda x: int(x) if x else None,
    }

    def __init__(
        self,
        name: str,
        address: str,
        type: str = "Residential",
        floor: int = 0,
        apartment: int = None,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(BUILDING_CSV) + 1
        self.name = name
        self.address = address
        self.floor = floor
        self.apartment = apartment
        self.type = type

        if save:
            self.save()

    def save(self):
        data = {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "floor": self.floor,
            "apartment": self.apartment if self.apartment is not None else "",
            "type": self.type,
        }
        append_dict_to_csv(BUILDING_CSV, data)

    def __str__(self):
        return f"Building({self.id}, {self.name}, {self.address}, Floor: {self.floor}, Apt: {self.apartment}, Type: {self.type})"

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, BUILDING_CSV, cls)
