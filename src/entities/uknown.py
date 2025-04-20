import datetime
from utils import (
    get_last_row_id,
    append_dict_to_csv,
    get_with_id,
    get_rows_where,
    create_or_update_row,
    del_rows_where,
)

UKNOWN_CSV = "data/Unknown.csv"


class Unknown:
    serialization = {
        "first_time_seen": lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"),
        "last_time_seen": lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"),
    }

    deserialization = {
        # "id": str,
        # "alarm_id": int,
        "first_time_seen": lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
        "last_time_seen": lambda s: datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
    }

    def __init__(
        self,
        alarm_id: int,
        first_time_seen: datetime.datetime = None,
        last_time_seen: datetime.datetime = None,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(UKNOWN_CSV) + 1
        self.alarm_id = alarm_id
        self.first_time_seen = (
            first_time_seen if first_time_seen else datetime.datetime.now()
        )
        self.last_time_seen = (
            last_time_seen if last_time_seen else datetime.datetime.now()
        )

        if save:
            self.save()

    def save(self):
        data = {}
        for key in ["id", "alarm_id", "first_time_seen", "last_time_seen"]:
            value = getattr(self, key)
            if key in self.serialization:
                value = self.serialization[key](value)
            data[key] = value

        append_dict_to_csv(UKNOWN_CSV, data)

    def __str__(self):
        return f"Unknown({self.id}, {self.alarm_id}, {self.first_time_seen}, {self.last_time_seen})"

    @staticmethod
    def get_with_id(id: int):
        return get_with_id(id, UKNOWN_CSV, Unknown)

    @staticmethod
    def get_rows_on_alarm_id(alarm_id: int):
        column_2_val = {
            "alarm_id": alarm_id,
        }
        return get_rows_where(UKNOWN_CSV, column_2_val, Unknown)

    @staticmethod
    def create_or_update_unknown(
        id: int,
        alarm_id: int,
        first_time_seen: datetime.datetime,
        last_time_seen: datetime.datetime,
    ):
        data_dict = {
            "id": id,
            "alarm_id": alarm_id,
            "first_time_seen": Unknown.serialization["first_time_seen"](
                first_time_seen
            ),
            "last_time_seen": Unknown.serialization["last_time_seen"](last_time_seen),
        }
        create_or_update_row(UKNOWN_CSV, data_dict, Unknown)

    @staticmethod
    def delete_on_id(id: int):
        column_2_val = {
            "id": id,
        }
        del_rows_where(UKNOWN_CSV, column_2_val)
