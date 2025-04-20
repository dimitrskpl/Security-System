from utils import get_last_row_id, append_dict_to_csv, get_with_id

ALERT_CONTACT_CSV = "data/AlertContact.csv"


class AlertContact:
    serialization = {}
    deserialization = {
        "id": int,
        "camera_id": int,
    }

    def __init__(
        self,
        camera_id: int,
        name: str,
        surname: str,
        email: str,
        phone: str,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(ALERT_CONTACT_CSV) + 1
        self.camera_id = camera_id
        self.name = name
        self.surname = surname
        self.email = email
        self.phone = phone

        if save:
            self.save()

    def save(self):
        data = {
            "id": self.id,
            "camera_id": self.camera_id,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "phone": self.phone,
        }
        append_dict_to_csv(ALERT_CONTACT_CSV, data)

    def __str__(self):
        return f"AlertContact({self.id}, {self.camera_id}, {self.name}, {self.surname}, {self.email}, {self.phone})"

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, ALERT_CONTACT_CSV, cls)
