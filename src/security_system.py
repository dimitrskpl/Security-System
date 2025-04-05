import face_recognition
import cv2
import numpy as np
import os
from alert import ALERT_LEVELS
from notification import NotificationEngine
from uknown import UnknownPersonTracker


class SecuritySystem:
    def __init__(
        self,
        img_folder=None,
        alert_timeout=30,
        forget_timeout=60,
        match_threshold=0.45,
        max_unknowns=10,
        alarm_duration=300,
        motion_sensitivity=5000,
    ):

        self.img_folder = img_folder
        self.tracker = UnknownPersonTracker(
            alert_timeout=alert_timeout,
            forget_timeout=forget_timeout,
            match_threshold=match_threshold,
            max_unknowns=max_unknowns,
            alarm_duration=alarm_duration,
        )
        self.motion_background = None
        self.motion_sensitivity = motion_sensitivity

        self.notifier = NotificationEngine()

        print("✅ Loading face encodings...")
        self.known_encodings, self.known_names = (
            self.load_encodings(img_folder) if img_folder else ([], [])
        )
        print("✅ Starting face recognition...")

    def load_encodings(self, img_folder="../test_img/"):
        known_encodings = []
        known_names = []
        for filename in os.listdir(img_folder):
            image_path = os.path.join(img_folder, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(filename)[0])
            else:
                print(f"⚠️ No face found in {filename}")

        if not known_encodings:
            raise ValueError("No valid face encodings found. Please check your images.")
        return np.array(known_encodings), known_names

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

    def motion_detected(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.motion_background is None:
            self.motion_background = gray
            return False

        frame_delta = cv2.absdiff(self.motion_background, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        motion_score = cv2.countNonZero(thresh)
        if motion_score > self.motion_sensitivity:
            self.motion_background = gray
            return True
        return False

    def get_face_loc_encodings(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame)
        # print(f"🧠 Detected {len(face_locations)} face(s)")
        encodings = []
        for face_location in face_locations:
            enc = face_recognition.face_encodings(rgb_frame, [face_location])
            if enc:
                encodings.append(enc[0])
        return face_locations, encodings

    def get_matches(self, face_encoding):
        matches = face_recognition.compare_faces(self.known_encodings, face_encoding)
        name = "Unknown"
        if matches:
            face_distances = face_recognition.face_distance(
                self.known_encodings, face_encoding
            )
            best_match_index = face_distances.argmin()
            if matches[best_match_index]:
                name = self.known_names[best_match_index]
        return name

    def system_alert(self, alerts, frame):
        for alert in alerts:
            print(str(alert))
            if alert.level == ALERT_LEVELS["High"]:
                snapshot = frame.copy()
                filename = f"snapshots/unknown_id_{alert.id}.jpg"
                os.makedirs("snapshots", exist_ok=True)
                cv2.imwrite(filename, snapshot)
        #         self.notifier.add_notification(Notification(alert, filename))

        # self.notifier.send_notifications()

    def start_face_recognition(
        self,
    ):
        cap = cv2.VideoCapture(0)
        print("✅ Face recognition running — press 'q' to quit.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            motion_detected = self.motion_detected(frame)
            if motion_detected:
                face_locations, encodings = self.get_face_loc_encodings(frame)

                for (top, right, bottom, left), face_encoding in zip(
                    face_locations, encodings
                ):

                    name = self.get_matches(face_encoding)

                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2
                    self.show_rect_label(frame, name, top, right, bottom, left)

                    alerts = (
                        self.tracker.update([face_encoding])
                        if name == "Unknown"
                        else []
                    )
                    if alerts:
                        self.system_alert(alerts, frame)
            else:
                # print(f"🛑 No motion detected, ignoring unknowns.")
                self.tracker.update_cleanup()

            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


def main():
    camera = SecuritySystem(
        # img_folder="../test_img/",
        img_folder="",
        alert_timeout=10,
        forget_timeout=20,
        match_threshold=0.45,
        max_unknowns=10,
        alarm_duration=15,
    )
    camera.start_face_recognition()


if __name__ == "__main__":
    main()
