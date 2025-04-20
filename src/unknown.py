import numpy as np
from utils import generate_id, save_snapshot, NULL_ENCODING
from alert import *
import face_recognition
import os

SNAPSHOTS_FOLDER = "snapshots"


class UnknownPersonTracker:
    def __init__(
        self,
        alert_after_sec=30,
        forget_after_sec=60,
        match_unknown_threshold=0.45,
        match_known_threshold=0.45,
        max_unknowns=10,
        max_encodings_per_person=5,
        active_alert=None,
    ):
        self.unknowns = []
        self.unknown_ids = set()
        self.unknown_encodings = []
        self.alert_after_sec = alert_after_sec
        self.forget_after_sec = forget_after_sec
        self.match_unknown_threshold = match_unknown_threshold
        self.match_known_threshold = match_known_threshold
        self.max_unknowns = max_unknowns
        self.max_encodings_per_person = max_encodings_per_person
        self.active_alert = active_alert

    def _find_similar(self, encoding, encodings, threshold):
        if not encodings:
            return None

        face_distances = face_recognition.face_distance(np.array(encodings), encoding)

        if len(face_distances) == 0:
            return None

        best_match_index = face_distances.argmin()
        best_distance = face_distances[best_match_index]

        if best_distance < threshold:
            return best_match_index

        return None

    def cleanup(self, update_time):
        to_delete_indices = [
            idx
            for idx in range(len(self.unknowns) - 1, -1, -1)
            if (
                not self.unknowns[idx].alerted
                and self.unknowns[idx].duration > self.forget_after_sec
            )
        ]
        if len(to_delete_indices):
            print(f"Deleting {len(to_delete_indices)} unknowns.")
            print(
                f"Before deletion: {len(self.unknowns)} unknowns, {len(self.unknown_encodings)} encodings, {len(self.unknown_ids)} ids."
            )
            self.del_unknowns(self, to_delete_indices)
            print(f"Deleted {len(to_delete_indices)} unknowns.")
            print(
                f"After deletion: {len(self.unknowns)} unknowns, {len(self.unknown_encodings)} encodings, {len(self.unknown_ids)} ids."
            )

        if self.active_alert and (
            (
                self.active_alert.update_time - self.active_alert.start_time
            ).total_seconds()
            > self.forget_after_sec
        ):
            self.active_alert = None
            print("⚠️ Alert expired, no unknowns detected.")
        # elif self.active_alert is not None:
        # print("⚠️ Alert still active, unknowns detected.")

    def update_durations(self, update_time):
        for person in self.unknowns:
            person.update_duration(update_time)

        if self.active_alert is not None:
            self.active_alert.update_time = update_time
            for person in self.active_alert.unknowns:
                person.update_duration(update_time)

    def update_cleanup(self, update_time):
        self.update_durations(update_time)
        self.cleanup(update_time)

    def del_unknowns(self, instance, unknown_indices):
        for unknown_idx in unknown_indices:
            for i in range(
                (unknown_idx + 1) * self.max_encodings_per_person - 1,
                unknown_idx * self.max_encodings_per_person - 1,
                -1,
            ):
                instance.unknown_encodings.pop(i)
        for unknown_idx in unknown_indices:
            instance.unknown_ids.remove(instance.unknowns[unknown_idx].id)
            instance.unknowns.pop(unknown_idx)

    def hash_encodings_idx(self, idx):
        return idx // self.max_encodings_per_person

    def update_seen_unknown(self, instance, idx, new_encoding, frame):
        unknown = instance.unknowns[idx]

        nxt_person_encoding_idx = unknown.get_total_encodings()
        if nxt_person_encoding_idx < self.max_encodings_per_person:
            instance.unknown_encodings[
                idx * self.max_encodings_per_person + nxt_person_encoding_idx
            ] = new_encoding

        unknown.add_snapshots_info([frame], [new_encoding])

    def single_update(self, new_encoding, update_time, frame):
        if self.active_alert is not None:
            enc_idx = self._find_similar(
                new_encoding,
                self.active_alert.unknown_encodings,
                self.match_unknown_threshold,
            )
            if enc_idx is not None:
                idx = self.hash_encodings_idx(enc_idx)
                self.update_seen_unknown(
                    self.active_alert,
                    idx,
                    new_encoding,
                    frame,
                )
                # print(f"Updated alarmed unknown: {self.active_alert.unknowns[idx].id}")
            else:
                self.add_unknown(
                    instance=self.active_alert,
                    encodings=[new_encoding],
                    update_time=update_time,
                    snapshots=[frame],
                )
                # print(f"Added unknown to alarm: {self.active_alert.unknowns[-1].id}")
                # print(f"Total alarmed unknowns: {len(self.active_alert.unknowns)}")
            return False

        enc_idx = self._find_similar(
            new_encoding, self.unknown_encodings, self.match_unknown_threshold
        )
        if enc_idx is not None:
            idx = self.hash_encodings_idx(enc_idx)
            self.update_seen_unknown(self, idx, new_encoding, frame)
            # print(f"Updated unknown: {self.unknowns[idx].id}")
            if not self.unknowns[idx].alerted and (
                self.unknowns[idx].duration > self.alert_after_sec
            ):
                return True
        else:
            self.add_unknown(
                instance=self,
                encodings=[new_encoding],
                update_time=update_time,
                snapshots=[frame],
            )
            # print(f"Added unknown: {self.unknowns[-1].id}")
            # print(f"Total non-alarmed unknowns: {len(self.unknowns)}")
        return False

    def add_unknown(self, instance, encodings, update_time, snapshots):
        if len(self.unknowns) >= self.max_unknowns:
            print(f"⚠️ Too many unknowns ({len(self.unknowns)}), ignoring new one.")
            return False
        unknown = UnknownPerson(
            encodings=encodings,
            first_seen=update_time,
            snapshots=snapshots,
            max_encodings=self.max_encodings_per_person,
        )
        instance.unknowns.append(unknown)
        instance.unknown_ids.add(instance.unknowns[-1].id)
        if len(encodings) < self.max_encodings_per_person:
            encodings.extend(
                [NULL_ENCODING] * (self.max_encodings_per_person - len(encodings))
            )
        instance.unknown_encodings.extend(encodings)

    def alert_all_unknowns(self, update_time):
        for unknown in self.unknowns:
            unknown.alert_person()

        self.active_alert = Alert(
            unknown_ids=self.unknown_ids,
            unknown_encodings=self.unknown_encodings,
            unknowns=self.unknowns,
            update_time=update_time,
        )

        self.unknown_encodings = []
        self.unknown_ids = set()
        self.unknowns = []

    def active_alert_exists(self):
        return self.active_alert is not None

    def update_after_new_knowns(self, new_known_encodings):
        if self.active_alert is not None:
            # print(
            #     f"⚠️ Alert still active, {len(self.active_alert.unknowns)} unknowns detected."
            # )
            # print(
            #     f"Updating alerted unknowns after new {len(new_known_encodings)} knowns."
            # )
            self.update_unknowns_after_new_knowns(
                self.active_alert, new_known_encodings
            )
            if len(self.active_alert.unknowns) == 0:
                self.deactivate_alert()
                print("⚠️ Alert deactivated, no unknowns detected.")
            else:
                print(f"⚠️ Alert still active")
        else:
            print("Updating alerted unknowns after new knowns.")
            self.update_unknowns_after_new_knowns(self, new_known_encodings)

    def update_unknowns_after_new_knowns(self, instance, new_known_encodings):
        to_delete_indices = []
        for idx in range(len(instance.unknowns) - 1, -1, -1):
            unknown = instance.unknowns[idx]
            for i in range(len(unknown.encodings)):
                if unknown.encodings[i] is not None:
                    enc_idx = self._find_similar(
                        unknown.encodings[i],
                        new_known_encodings,
                        self.match_known_threshold,
                    )
                    if enc_idx is not None:
                        to_delete_indices.append(idx)
                        break
        if len(to_delete_indices) > 0:
            self.del_unknowns(instance, to_delete_indices)

    def deactivate_alert(self):
        self.active_alert = None


class UnknownPerson:
    def __init__(
        self,
        encodings,
        first_seen,
        snapshots,
        max_encodings=5,
        id=None,
        alerted=False,
        all_encodings_saved=False,
        all_img_saved=False,
        img_paths=[],
    ):
        self.id = generate_id() if id is None else id
        self.encodings = encodings[:max_encodings]
        self.first_seen = first_seen
        self.last_seen = first_seen
        self.alerted = alerted
        self.duration = 0
        self.snapshots = snapshots[:max_encodings]
        self.max_encodings = max_encodings
        self.unsaved_encodings_indices = (
            list(range(0, len(encodings))) if not all_encodings_saved else []
        )
        self.unsaved_images_indices = (
            list(range(0, len(encodings))) if not all_img_saved else []
        )
        self.img_paths = img_paths

    def empty_unsaved_encodings_indices(self):
        self.unsaved_encodings_indices = []
        self.all_encodings_saved = True

    def empty_unsaved_images_indices(self):
        self.unsaved_images_indices = []
        self.all_img_saved = True

    def alert_person(self):
        self.alerted = True

    def save_snapshots(self, snapshot_folder):
        snapshots_ids = []
        for i in self.unsaved_images_indices:
            snapshot_id = generate_id()
            snapshots_ids.append(snapshot_id)
            filename = os.path.join(
                snapshot_folder, f"unknown_{self.id}_{snapshot_id}.jpg"
            )
            save_snapshot(self.snapshots[i], filename)
            self.img_paths.append(filename)
        self.empty_unsaved_images_indices()
        return snapshots_ids

    def update_duration(self, last_seen):
        self.last_seen = last_seen
        self.duration = (self.last_seen - self.first_seen).total_seconds()
        return self.duration

    def add_snapshots_info(self, snapshots, encodings):
        add_encodings = self.max_encodings - len(self.encodings)
        if add_encodings > 0:
            self.unsaved_encodings_indices.extend(
                list(range(len(self.encodings), len(self.encodings) + len(encodings)))
            )
            self.unsaved_images_indices.extend(
                list(range(len(self.snapshots), len(self.snapshots) + len(snapshots)))
            )
            self.snapshots.extend(snapshots[:add_encodings])
            self.encodings.extend(encodings[:add_encodings])

    def get_total_encodings(self):
        return len(self.encodings)
