from utils import get_last_row_id, append_dict_to_csv, get_with_id

CAMERA_ADMIN_CSV = "data/CameraAdmin.csv"


class CameraAdmin:
    serialization = {}
    deserialization = {
        "id": int,
    }

    def __init__(
        self,
        name: str,
        surname: str,
        email: str,
        phone: str,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(CAMERA_ADMIN_CSV) + 1
        self.name = name
        self.surname = surname
        self.email = email
        self.phone = phone

        if save:
            self.save()

    def save(self):
        data = {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "phone": self.phone,
        }
        append_dict_to_csv(CAMERA_ADMIN_CSV, data)

    def __str__(self):
        return f"CameraAdmin({self.id}, {self.name}, {self.surname}, {self.email}, {self.phone})"

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, CAMERA_ADMIN_CSV, cls)
