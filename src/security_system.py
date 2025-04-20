# import face_recognition
import cv2
import numpy as np
import os
from alert import ALERT_STATUS_CODE_2_LABEL, ALERT_LABEL_2_CODE
import time
import datetime

# from notification import NotificationEngine
from unknown import UnknownPersonTracker
from request_handler import RequestHandler
from motion_detector import MotionDetector
from db import DBInterface
from utils import FaceRecognition

SNAPSHOT_ALERT_FOLDER = "data/snapshots/alerts"
SNAPSHOT_UKNOWN_FOLDER = "data/snapshots/unknowns"


class SecuritySystem:
    def __init__(
        self,
        camera_id,
        known_faces_folder=None,
        alert_after_sec=30,
        forget_after_sec=60,
        match_unknown_threshold=0.45,
        match_known_threshold=0.45,
        max_unknowns=10,
        motion_sensitivity=5000,
        enable_notification=False,
        max_encodings_per_person=5,
        check_db_update_per_sec=60,
        update_db_active_alert_per_sec=10,
    ):
        os.makedirs(SNAPSHOT_ALERT_FOLDER, exist_ok=True)
        os.makedirs(SNAPSHOT_UKNOWN_FOLDER, exist_ok=True)
        self.camera_id = camera_id
        self.known_faces_folder = known_faces_folder
        self.match_known_threshold = match_known_threshold
        self.enable_notification = enable_notification
        self.check_db_update_per_sec = check_db_update_per_sec
        self.update_db_active_alert_per_sec = update_db_active_alert_per_sec

        self.db = DBInterface()
        print("✅ Loading face encodings...")
        self.encoding_2_name = self.db.get_known_faces_name_encodings(
            camera_id=camera_id
        )
        self.known_encodings = (
            np.array(list(self.encoding_2_name.keys()))
            if self.encoding_2_name
            else np.empty((0, 128), dtype=np.float64)
        )

        self.known_names = list(self.encoding_2_name.values())
        print(f"✅ Loaded {len(self.known_names)} known faces")

        active_alert = self.db.get_latest_alarm_info(
            self.camera_id, max_encodings_per_person
        )

        if active_alert is not None:
            print(
                f"Loading alarm with id: {active_alert.id}, status: {ALERT_STATUS_CODE_2_LABEL[active_alert.status]}"
            )
            self.alarm_saved = True
            self.alarm_updated_db_time = active_alert.update_time
        else:
            print("No active or pending alarm found")
            self.alarm_saved = False
            self.alarm_updated_db_time = None

        self.tracker = UnknownPersonTracker(
            alert_after_sec=alert_after_sec,
            forget_after_sec=forget_after_sec,
            match_unknown_threshold=match_unknown_threshold,
            match_known_threshold=match_known_threshold,
            max_unknowns=max_unknowns,
            max_encodings_per_person=max_encodings_per_person,
            active_alert=active_alert,
        )

        self.motion_detector = MotionDetector(sensitivity=motion_sensitivity)

        pending_alarm_ids = self.db.get_pending_alarm_ids(camera_id)

        self.face_recognition_util = FaceRecognition()
        self.request_handler = RequestHandler(
            camera_id=self.camera_id,
            db=self.db,
            pending_alarm_ids=pending_alarm_ids,
            face_recognition_util=self.face_recognition_util,
        )
        self.last_check_make_updates_time = time.time()
        # self.request_handler.listen_loop()

        # self.notifier = NotificationEngine()

        print("✅ Starting Security System...")

    def add_new_known_faces(self, names, new_encodings):
        self.known_names += names
        self.known_encodings = np.concatenate(
            [self.known_encodings, np.array(new_encodings)]
        )

    def check_make_updates(self):
        updated_alarms = self.request_handler.get_updated_alarm_ids_status()
        if self.tracker.active_alert is not None:
            for alarm_id, status in updated_alarms:
                if alarm_id == self.tracker.active_alert.id:
                    if status == 0:
                        print("✅ Alarm resolved")
                        self.tracker.deactivate_alert()
                    elif status == 1:
                        print("✅ Alarm still active")
                    elif status == 2:
                        raise ValueError("Alarm still PENDING")

        updated_known_names_encodings = self.request_handler.get_new_known_faces()
        if updated_known_names_encodings:
            new_names = [item[0] for item in updated_known_names_encodings]
            new_encodings = [item[1] for item in updated_known_names_encodings]
            print(f"✅ Received {len(new_names)} new known faces: {new_names}")
            self.add_new_known_faces(new_names, new_encodings)
            active_alert_id = (
                self.tracker.active_alert.id if self.tracker.active_alert else None
            )
            self.tracker.update_after_new_knowns(new_encodings)
            if active_alert_id and not self.tracker.active_alert_exists():
                self.request_handler.del_pending_alert(active_alert_id)
                self.db.updateAlarmStatus(active_alert_id, ALERT_LABEL_2_CODE["False"])
                self.db.rm_uknowns_on_alarm_id(active_alert_id, self.camera_id)

    def show_rect_label(self, frame, name, top, right, bottom, left, style="simple"):
        if style == "simple":
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(
                frame,
                name,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
        else:
            cv2.rectangle(
                frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED
            )
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(
                frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1
            )

    def get_matches(self, face_encoding):
        best_match_index, best_distance = (
            self.face_recognition_util.get_best_distance_idx(
                self.known_encodings, face_encoding
            )
        )

        if best_match_index is not None and best_distance < self.match_known_threshold:
            return self.known_names[best_match_index]
        else:
            return "Unknown"

    def system_alert(self, alert, frame):
        if not self.alarm_saved:
            print(str(alert))
            self.request_handler.add_pending_alert(alert.id)
            snapshot = frame.copy()
            filename = os.path.join(SNAPSHOT_ALERT_FOLDER, f"alert_{alert.id}.jpg")
            cv2.imwrite(filename, snapshot)
            self.db.createAlarm(
                self.camera_id,
                alert.start_time,
                alert.update_time,
                filename,
                alarm_id=alert.id,
            )
        else:
            print(f"Updating alert: {alert.id}, update time: {alert.update_time}")
            self.db.updateAlarmUpdateTime(
                alarm_id=alert.id,
                last_time_seen=alert.update_time,
            )
        for unknown in alert.unknowns:
            snapshots_ids = unknown.save_snapshots(SNAPSHOT_UKNOWN_FOLDER)
            self.db.createOrUpdateUnknown(
                alarm_id=alert.id,
                first_time_seen=unknown.first_seen,
                last_time_seen=unknown.last_seen,
                id=unknown.id,
            )
            for i, idx in enumerate(unknown.unsaved_encodings_indices):
                self.db.createUnknownFaceEncoding(
                    unknown_face_id=unknown.id,
                    encoding=unknown.encodings[idx],
                    img_path=unknown.img_paths[idx],
                    id=snapshots_ids[i],
                )
            unknown.empty_unsaved_encodings_indices()
            # self.tracker.add_unknown(unknown)
            # self.tracker.add_snapshot(unknown, filename)
        # self.notifier.add_notification(Notification(alert, filename))

        # self.notifier.send_notifications()
        self.alarm_saved = True
        self.alarm_updated_db_time = alert.update_time

    def start_face_recognition(
        self,
    ):
        cap = cv2.VideoCapture(0)
        print("✅ Face recognition running — press 'q' to quit.")

        while True:
            if (
                time.time() - self.last_check_make_updates_time
                > self.check_db_update_per_sec
            ):
                self.check_make_updates()
                self.last_check_make_updates_time = time.time()
                print(
                    f"✅ Checked for updates at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

            ret, frame = cap.read()
            if not ret:
                break
            orig_frame = frame.copy()
            frame_timestamp = datetime.datetime.now()
            motion_detected = self.motion_detector.detect_motion(frame)
            if motion_detected:

                self.tracker.update_cleanup(update_time=frame_timestamp)

                self.alarm_saved = True if self.tracker.active_alert_exists() else False
                face_locations, encodings = (
                    self.face_recognition_util.get_face_loc_encodings(frame)
                )  # self.get_face_loc_encodings(frame)
                alerted = False
                for (top, right, bottom, left), face_encoding in zip(
                    face_locations, encodings
                ):

                    name = self.get_matches(face_encoding)

                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2
                    self.show_rect_label(frame, name, top, right, bottom, left)

                    if name == "Unknown":
                        alerted = alerted or self.tracker.single_update(
                            face_encoding, frame_timestamp, frame
                        )
                if not self.tracker.active_alert_exists() and alerted:
                    print("🚨 Alert triggered!")
                    self.tracker.alert_all_unknowns(update_time=frame_timestamp)

                if self.tracker.active_alert_exists():
                    if not self.alarm_saved or (
                        self.alarm_saved
                        and (
                            datetime.datetime.now() - self.alarm_updated_db_time
                        ).total_seconds()
                        > self.update_db_active_alert_per_sec
                    ):
                        self.check_make_updates()
                        if self.tracker.active_alert_exists():
                            self.system_alert(self.tracker.active_alert, orig_frame)

            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.review_manager.stop()


def main():
    camera = SecuritySystem(
        camera_id=0,
        known_faces_folder="data/known_face_images/",
        alert_after_sec=5,
        forget_after_sec=30,
        check_db_update_per_sec=10,
        update_db_active_alert_per_sec=15,
        match_unknown_threshold=0.6,
        match_known_threshold=0.5,
        max_unknowns=10,
        enable_notification=False,
        max_encodings_per_person=5,
    )
    camera.start_face_recognition()


if __name__ == "__main__":
    main()
