from utils import append_dict_to_csv, get_with_id

CAMERA_2_ADMIN_CSV = "data/Camera2Admin.csv"


class Camera2Admin:
    serialization = {}
    deserialization = {
        "admin_id": int,
        "camera_id": int,
    }

    def __init__(
        self,
        camera_id: int,
        admin_id: str,
        save: bool = True,
    ):
        self.camera_id = camera_id
        self.admin_id = admin_id

        if save:
            self.save()

    def save(self):
        data = {
            "camera_id": self.camera_id,
            "admin_id": self.admin_id,
        }
        append_dict_to_csv(CAMERA_2_ADMIN_CSV, data)

    def __str__(self):
        return f"Camera2Admin({self.admin_id}, {self.camera_id})"

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, CAMERA_2_ADMIN_CSV, cls)
