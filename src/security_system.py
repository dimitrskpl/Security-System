import face_recognition
import cv2
import numpy as np
import os
import time
import uuid

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


class Alert:
    def __init__(self, message, level):
        self.message = message
        self.timestamp = time.time()
        self.level = level  # high, medium, low

    def __str__(self):
        return f"Alert: {self.message} at {time.ctime(self.timestamp)}"


class UnknownPersonTracker:
    def __init__(
        self,
        timeout=30,
        match_threshold=0.45,
        max_unknowns=10,
        frames_threshold=10,
        alarm_duration=300,
    ):
        self.unknowns = {}
        self.timeout = timeout  # seconds to consider someone suspicious
        self.match_threshold = match_threshold
        self.max_unknowns = max_unknowns
        self.frames_threshold = frames_threshold
        self.alarm_duration = alarm_duration

    def _generate_id(self):
        return str(uuid.uuid4())[:8]

    def _find_similar(self, encoding):
        for uid, data in self.unknowns.items():
            dist = np.linalg.norm(data.encoding - encoding)
            # if dist < self.match_threshold:
            return uid
        return None

    def cleanup(self):
        to_delete = [
            uid
            for uid, un_person in self.unknowns.items()
            if un_person.duration > self.timeout
            and not un_person.alerted
            or un_person.alerted
            and un_person.duration > self.alarm_duration
        ]
        for uid in to_delete:
            del self.unknowns[uid]

    def update(self, new_encodings):
        self.cleanup()

        if not len(new_encodings):
            return None

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
                and self.unknowns[uid].frames_seen >= self.frames_threshold
            ):
                alert = self.unknowns[uid].alert_()
        else:
            alert = None
            new_id = self._generate_id()
            self.unknowns[new_id] = UnknownPerson(
                encoding=new_encoding,
                first_seen=now,
            )

        return alert


class UnknownPerson:
    def __init__(self, encoding, first_seen):
        self.encoding = encoding
        self.first_seen = first_seen
        self.last_seen = first_seen
        self.frames_seen = 1
        self.alerted = False
        self.duration = 0
        self.alert = None

    def update(self):
        self.last_seen = time.time()
        self.frames_seen += 1
        self.duration = self.last_seen - self.first_seen
        self.alert = Alert(
            f"Unknown person detected for {self.duration} seconds.",
            ALERT_LEVELS["Low"],
        )

    def alert_(self):
        self.alerted = True
        self.alert = Alert(
            f"Alert, Unknown person detected for {self.duration} seconds.",
            ALERT_LEVELS["High"],
        )
        return self.alert


class SecuritySystem:
    def __init__(
        self,
        img_folder=None,
        timeout=30,
        match_threshold=0.45,
        max_unknowns=10,
        frames_threshold=1,
        alarm_duration=300,
    ):

        self.img_folder = img_folder
        self.tracker = UnknownPersonTracker(
            timeout=timeout,
            match_threshold=match_threshold,
            max_unknowns=max_unknowns,
            frames_threshold=frames_threshold,
            alarm_duration=alarm_duration,
        )
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

    def start_face_recognition(
        self,
    ):
        known_encodings = self.known_encodings
        known_names = self.known_names
        cap = cv2.VideoCapture(0)
        print("✅ Face recognition running — press 'q' to quit.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_frame)
            print(f"🧠 Detected {len(face_locations)} face(s)")
            encodings = []
            for face_location in face_locations:
                enc = face_recognition.face_encodings(rgb_frame, [face_location])
                if enc:
                    encodings.append(enc[0])

            for (top, right, bottom, left), face_encoding in zip(
                face_locations, encodings
            ):
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                name = "Unknown"
                if matches:
                    face_distances = face_recognition.face_distance(
                        known_encodings, face_encoding
                    )
                    best_match_index = face_distances.argmin()
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                else:
                    alerts = self.tracker.update([face_encoding])
                    if alerts:
                        for alert in alerts:
                            print(alert.message)
                            print(f"⚠️ Alert level: {ALERT_LEVELS_DISPLAY[alert.level]}")

                top *= 2
                right *= 2
                bottom *= 2
                left *= 2
                self.show_rect_label(frame, name, top, right, bottom, left)

            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


def main():
    camera = SecuritySystem(
        img_folder="",
        timeout=10,
        match_threshold=0.45,
        max_unknowns=10,
        frames_threshold=10,
        alarm_duration=15,
    )
    camera.start_face_recognition()


if __name__ == "__main__":
    main()
