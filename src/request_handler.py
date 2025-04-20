import os
import time
import threading
from typing import List
from utils import create_csv_if_not_exists, FaceRecognition
from db import DBInterface

ALARM_INPUT_CSV = "data/AlarmInput.csv"
NEW_KNOWN_INPUT_CSV = "data/NewKnownInput.csv"


class RequestHandler:
    def __init__(
        self,
        camera_id: int,
        db: DBInterface,
        pending_alarm_ids: List,
        face_recognition_util: FaceRecognition,
    ):
        self.camera_id = camera_id
        self.pending_alarm_ids = pending_alarm_ids
        self.updated_alarm_ids_status = []
        self.updated_known_names_encodings = []

        self.running = True
        self.alarm_request_input_file = ALARM_INPUT_CSV
        self.new_known_face_input_file = NEW_KNOWN_INPUT_CSV
        create_csv_if_not_exists(self.alarm_request_input_file, ["alarm_id", "status"])
        create_csv_if_not_exists(self.new_known_face_input_file, ["name", "img_path"])
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()
        self.updated_alarm_lock = threading.Lock()
        self.updated_known_names_encodings_lock = threading.Lock()
        self.db = db
        self.alarm_request_input_file_lock = threading.Lock()
        self.new_known_face_input_file_lock = threading.Lock()
        self.pending_alarm_ids_lock = threading.Lock()
        self.face_recognition_util = face_recognition_util

    def add_pending_alert(self, alert_id):
        with self.pending_alarm_ids_lock:
            self.pending_alarm_ids.append(alert_id)
        with self.alarm_request_input_file_lock:
            try:
                with open(self.alarm_request_input_file, "a") as f:
                    f.write(f"{alert_id},2\n")
                print(f"🕒 Alert {alert_id} is now pending for review...")
            except Exception as e:
                print(f"❌ Failed to create pending alarm row for response: {e}")

    def add_new_known_face(self, name, img_enc):
        # get lock
        with self.updated_known_names_encodings_lock:
            self.updated_known_names_encodings.append((name, img_enc))
            print(f"✅ Added new known face: {name} in updated_known_names_encodings")

    def add_updated_alarm(self, alarm_id, status):
        with self.updated_alarm_lock:
            self.updated_alarm_ids_status.append((alarm_id, status))
            print(f"✅ Added updated alarm: {alarm_id} in updated_alarm_ids_status")

    def get_new_known_faces(self):
        print("🕒 Getting new known faces...")
        with self.updated_known_names_encodings_lock:
            updated_known_names_encodings = self.updated_known_names_encodings
            self.updated_known_names_encodings = []
            return updated_known_names_encodings

    def get_updated_alarm_ids_status(self):
        print("🕒 Getting updated alarm ids status...")
        with self.updated_alarm_lock:
            updated_alarm_ids_status = self.updated_alarm_ids_status
            self.updated_alarm_ids_status = []
            return updated_alarm_ids_status

    def del_pending_alert(self, alarm_id):
        with self.pending_alarm_ids_lock:
            if alarm_id in self.pending_alarm_ids:
                self.pending_alarm_ids.remove(alarm_id)
            else:
                print(f"⚠️ Tried to remove non-existent pending alarm: {alarm_id}")

        with self.alarm_request_input_file_lock:
            try:
                with open(self.alarm_request_input_file, "r") as f:
                    lines = f.readlines()

                remaining_lines = [lines[0]]  # keep the header line
                for line in lines[1:]:
                    if line.strip().split(",")[0] != alarm_id:
                        remaining_lines.append(line)

                with open(self.alarm_request_input_file, "w") as f:
                    f.writelines(remaining_lines)

            except Exception as e:
                print(f"❌ Failed to delete pending alarm row for response: {e}")

    def listen_for_pending_alerts(self):
        with self.alarm_request_input_file_lock:
            try:
                with open(self.alarm_request_input_file, "r") as f:
                    lines = f.readlines()

                remaining_lines = [lines[0]]  # keep the header line
                for line in lines[1:]:
                    alarm_id, status = line.strip().split(",")
                    status = int(status)
                    if status != 2:
                        self.update_alert_status_db(alarm_id, status)
                        if status == 0:
                            self.db.mv_uknowns_to_knowns(alarm_id, self.camera_id)
                        self.add_updated_alarm(alarm_id, status)
                    else:
                        remaining_lines.append(line)

                if len(lines) > 1:
                    with open(self.alarm_request_input_file, "w") as f:
                        f.writelines(remaining_lines)

            except FileNotFoundError:
                print("No pending alarms found.")

    def listen_for_new_known_faces(self):
        with self.new_known_face_input_file_lock:
            try:
                with open(self.new_known_face_input_file, "r") as f:
                    lines = f.readlines()

                for line in lines[1:]:
                    name, img_path = line.strip().split(",")
                    known_face = self.db.createKnownFace(self.camera_id, name)
                    encoding = self.face_recognition_util.get_face_encodings(img_path)

                    if encoding is not None:
                        known_face_encoding = self.db.createKnownFaceEncoding(
                            known_face.id, img_path, encoding
                        )
                        self.add_new_known_face(name, encoding)

                if len(lines) > 1:
                    # Clear the file after processing
                    with open(self.new_known_face_input_file, "w") as f:
                        f.write(lines[0])  # keep the header line

            except Exception as e:
                print(f"Error processing new known faces: {e}")

    def update_alert_status_db(self, alarm_id, status):
        self.db.updateAlarmStatus(alarm_id, status)

    def listen_loop(self):
        while self.running:
            time.sleep(3)
            self.listen_for_pending_alerts()
            self.listen_for_new_known_faces()

    def stop(self):
        self.running = False
        self.thread.join()
