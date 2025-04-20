import time
from utils import generate_id

ALERT_LEVELS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
}

ALERT_LEVELS_DISPLAY = {
    1: "Low",
    2: "Medium",
    3: "High",
}

ALERT_SYMBOLS = {
    1: "ℹ️",
    2: "⚠️",
    3: "🚨",
}

ALERT_STATUS_CODE_2_LABEL = {
    0: "False",
    1: "True",
    2: "Pending",
}

ALERT_LABEL_2_CODE = {v: k for k, v in ALERT_STATUS_CODE_2_LABEL.items()}


class Alert:
    def __init__(
        self,
        unknown_ids,
        unknown_encodings,
        unknowns,
        update_time,
        id=None,
        start_time=None,
        status=ALERT_LABEL_2_CODE["Pending"],
    ):
        self.id = generate_id() if id is None else id
        self.unknown_ids = unknown_ids
        self.unknown_encodings = unknown_encodings
        self.unknowns = unknowns
        self.start_time = update_time if start_time is None else start_time
        self.update_time = update_time
        self.status = status

    def __str__(self):
        return f"🚨 Alert! {len(self.unknown_ids)} unknown people detected. Alert started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} and updated at {self.update_time.strftime('%Y-%m-%d %H:%M:%S')}"
