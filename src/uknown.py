import numpy as np
import time
import uuid
from alert import *


class UnknownPersonTracker:
    def __init__(
        self,
        alert_timeout=30,
        forget_timeout=60,
        match_threshold=0.45,
        max_unknowns=10,
        alarm_duration=300,
    ):
        self.unknowns = {}
        self.alert_timeout = alert_timeout
        self.forget_timeout = forget_timeout
        self.match_threshold = match_threshold
        self.max_unknowns = max_unknowns
        self.alarm_duration = alarm_duration

    def _generate_id(self):
        return str(uuid.uuid4())[:8]

    def _find_similar(self, encoding):
        for uid, data in self.unknowns.items():
            dist = np.linalg.norm(data.encoding - encoding)
            if dist < self.match_threshold:
                return uid
        return None

    def cleanup(self):
        to_delete = [
            uid
            for uid, un_person in self.unknowns.items()
            if un_person.duration > self.forget_timeout
            and not un_person.alerted
            or un_person.alerted
            and un_person.duration > self.alarm_duration
        ]
        for uid in to_delete:
            del self.unknowns[uid]

    def update_duarations(self):
        for person in self.unknowns.values():
            person.update_duration()

    def update_cleanup(self):
        self.update_duarations()
        self.cleanup()

    def update(self, new_encodings):
        self.update_cleanup()
        if not len(new_encodings):
            return None

        print(f"Total unknowns: {len(self.unknowns)}")
        if len(self.unknowns) >= self.max_unknowns:
            print("⚠️ Too many unknowns, ignoring new one.")
            return []

        now = time.time()
        alerts = []
        for new_encoding in new_encodings:
            alert = self.single_update(new_encoding, now)
            if alert:
                alerts.append(alert)
        return alerts

    def single_update(self, new_encoding, now):
        uid = self._find_similar(new_encoding)
        if uid:
            alert = self.unknowns[uid].update()
            if (
                not self.unknowns[uid].alerted
                and self.unknowns[uid].duration >= self.alert_timeout
            ):
                alert = self.unknowns[uid].alert_()
        else:
            alert = None
            new_id = self._generate_id()
            self.unknowns[new_id] = UnknownPerson(
                id=new_id,
                encoding=new_encoding,
                first_seen=now,
            )

        return alert


class UnknownPerson:
    def __init__(self, id, encoding, first_seen):
        self.id = id
        self.encoding = encoding
        self.first_seen = first_seen
        self.last_seen = first_seen
        self.frames_seen = 1
        self.alerted = False
        self.duration = 0
        self.alert = Alert(id, f"New unknown person detected", ALERT_LEVELS["Low"])

    def update(self):
        self.update_duration()
        self.frames_seen += 1
        self.alert = Alert(
            self.id,
            f"Unknown person detected for {self.duration} seconds.",
            ALERT_LEVELS["Medium"],
        )
        return self.alert

    def alert_(self):
        self.alerted = True
        self.alert = Alert(
            self.id,
            f"Alert, Unknown person detected for {self.duration} seconds.",
            ALERT_LEVELS["High"],
        )
        return self.alert

    def update_duration(self):
        self.last_seen = time.time()
        self.duration = self.last_seen - self.first_seen
        return self.duration
