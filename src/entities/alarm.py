from utils import (
    get_last_row_id,
    append_dict_to_csv,
    get_with_id,
    get_rows_where,
    update_row_by_id,
)
import datetime

ALARM_CSV = "data/Alarm.csv"


class Alarm:
    serialization = {
        "start_date_time": lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"),
        "update_time": lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"),
    }

    deserialization = {
        "id": str,
        "camera_id": int,
        "status": int,
        "start_date_time": lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
        "update_time": lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
    }

    def __init__(
        self,
        camera_id: int,
        status: int = 2,
        start_date_time: datetime.datetime = None,
        update_time: datetime.datetime = None,
        snapshot_path: str = None,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(ALARM_CSV) + 1
        self.camera_id = camera_id
        self.status = status
        self.start_date_time = start_date_time or datetime.datetime.now()
        self.update_time = update_time or datetime.datetime.now()
        self.snapshot_path = snapshot_path

        if save:
            self.save()

    def save(self):
        data = {
            "id": self.id,
            "camera_id": self.camera_id,
            "status": self.status,
            "start_date_time": self.serialization["start_date_time"](
                self.start_date_time
            ),
            "update_time": self.serialization["update_time"](self.update_time),
            "snapshot_path": self.snapshot_path,
        }
        append_dict_to_csv(ALARM_CSV, data)

    def __str__(self):
        return (
            f"Alarm(id={self.id}, camera_id={self.camera_id}, status={self.status}, "
            f"start={self.start_date_time}, update={self.update_time}, snapshot={self.snapshot_path})"
        )

    @classmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, ALARM_CSV, cls)

    @staticmethod
    def get_pending_alarms_rows_on_camera_id(camera_id: int):
        column_2_val = {
            "camera_id": camera_id,
            "status": 2,
        }
        return get_rows_where(ALARM_CSV, column_2_val, Alarm)

    @staticmethod
    def get_active_alarms_rows_on_camera_id(camera_id: int):
        column_2_val = {
            "camera_id": camera_id,
            "status": 1,
        }
        return get_rows_where(ALARM_CSV, column_2_val, Alarm)

    @staticmethod
    def update_alarm_update_time(alarm_id: int, update_time: datetime.datetime):
        return update_row_by_id(
            ALARM_CSV,
            alarm_id,
            {"update_time": Alarm.serialization["update_time"](update_time)},
        )

    @staticmethod
    def update_alarm_status(alarm_id: int, status: int):
        return update_row_by_id(
            ALARM_CSV,
            alarm_id,
            {"status": status},
        )
