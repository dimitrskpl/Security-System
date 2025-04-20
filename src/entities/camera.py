from utils import get_last_row_id, append_dict_to_csv, get_with_id

CAMERA_CSV = "data/Camera.csv"


class Camera:
    deserialization = {
        "id": int,
        "building_id": int,
    }

    def __init__(
        self,
        building_id: int,
        type: str,
        camera_address: str,
        usage_desc: str,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(CAMERA_CSV) + 1
        self.building_id = building_id
        self.type = type
        self.camera_address = camera_address
        self.usage_desc = usage_desc

        if save:
            self.save()

    def save(self):
        data = {
            "id": self.id,
            "building_id": self.building_id,
            "type": self.type,
            "camera_address": self.camera_address,
            "usage_desc": self.usage_desc,
        }
        append_dict_to_csv(CAMERA_CSV, data)

    def __str__(self):
        return (
            f"Camera(id={self.id}, building_id={self.building_id}, "
            f"type={self.type}, address={self.camera_address}, usage='{self.usage_desc}')"
        )

    @classmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, CAMERA_CSV, cls)
