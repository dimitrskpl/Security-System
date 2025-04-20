from utils import (
    get_last_row_id,
    append_dict_to_csv,
    get_with_id,
    get_rows_where,
    generate_id,
)

KNOWN_FACE_CSV = "data/KnownFace.csv"


class KnownFace:
    serialization = {}
    deserialization = {
        "camera_id": int,
    }

    def __init__(
        self,
        camera_id: int,
        display_name: str,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else generate_id()
        self.camera_id = camera_id
        self.display_name = display_name

        if save:
            self.save()

    def save(self):
        data = {
            "id": self.id,
            "camera_id": self.camera_id,
            "display_name": self.display_name,
        }
        append_dict_to_csv(KNOWN_FACE_CSV, data)

    def __str__(self):
        return f"KnownFace({self.id}, {self.camera_id}, {self.display_name})"

    @staticmethod
    def get_rows_on_camera_id(camera_id: int):
        column_2_val = {
            "camera_id": camera_id,
        }
        return get_rows_where(KNOWN_FACE_CSV, column_2_val, KnownFace)

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, KNOWN_FACE_CSV, cls)
