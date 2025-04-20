from entities.camera_admin import CameraAdmin
from entities.alert_contact import AlertContact
from entities.known_face import KnownFace
from entities.camera import Camera
from entities.known_face_encoding import KnownFaceEncoding
from entities.admin_2_camera import Camera2Admin
from entities.building import Building
from entities.alarm import Alarm
from entities.uknown import Unknown
from entities.unknown_face_encoding import UnknownFaceEncoding
from utils import get_face_encodings, NULL_ENCODING, generate_id
from unknown import UnknownPerson
from alert import Alert
import os


class DBInterface:
    def createCameraAdmin(self, name, surname, email, phone):
        camera_admin = CameraAdmin(name, surname, email, phone)
        print(f"Camera Admin created: {str(camera_admin)}")
        return camera_admin

    def createBuilding(self, name, address, type, floor, apartment):
        building = Building(name, address, type, floor, apartment)
        print(f"Building created: {str(building)}")
        return building

    def createCamera(self, building_id, type, camera_address, usage_desc):
        camera = Camera(building_id, type, camera_address, usage_desc)
        print(f"Camera created: {str(camera)}")
        return camera

    def relate_camera_admin_to_camera(self, camera_id, admin_id):
        relation = Camera2Admin(camera_id, admin_id)
        print(f"Relation created: {str(relation)}")
        return relation

    def createAlertContact(self, camera_id, name, surname, email, phone):
        alert_contact = AlertContact(camera_id, name, surname, email, phone)
        print(f"Alert Contact created: {str(alert_contact)}")
        return alert_contact

    def createKnownFace(self, camera_id, display_name):
        known_face = KnownFace(camera_id, display_name)
        print(f"Known Face created: {str(known_face)}")
        return known_face

    def createKnownFaceEncoding(self, known_face_id, img_path, encoding):
        known_face_encoding = KnownFaceEncoding(known_face_id, encoding, img_path)
        print(f"Known Face Encoding created: {str(known_face_encoding)}")
        return known_face_encoding

    # def createKnownFaceEncoding(self, known_face_id, img_path):
    #     print(f"computing encoding for {img_path}")
    #     if not os.path.exists(img_path):
    #         print(f"Image path {img_path} does not exist.")
    #         return None
    #     encoding = get_face_encodings(img_path)
    #     if encoding is None:
    #         print(f"No face found in image {img_path}.")
    #         return None
    #     else:
    #         print(f"Encoding for {img_path} computed successfully.")
    #     known_face_encoding = KnownFaceEncoding(known_face_id, encoding, img_path)
    #     print(f"Known Face Encoding created: {str(known_face_encoding)}")
    #     return known_face_encoding

    def createKnownFaceEncodings(self, known_face_id, img_folder_path):
        files = os.listdir(img_folder_path)
        files = [
            f
            for f in files
            if f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".png")
        ]
        known_face_encodings = []
        for file in files:
            img_path = os.path.join(img_folder_path, file)
            encoding = get_face_encodings(img_path)
            known_face_encoding = KnownFaceEncoding(known_face_id, encoding, img_path)
            print(f"Known Face Encoding created: {str(known_face_encoding)}")
            known_face_encodings.append(known_face_encoding)
        return known_face_encodings

    def createAlarm(
        self,
        camera_id,
        start_date_time,
        update_time,
        snapshot_path,
        status=2,
        alarm_id=None,
    ):
        alarm = Alarm(
            id=alarm_id,
            camera_id=camera_id,
            status=status,
            start_date_time=start_date_time,
            update_time=update_time,
            snapshot_path=snapshot_path,
        )
        print(f"Alarm created: {str(alarm)}")
        return alarm

    def createUnknown(self, alarm_id, first_time_seen, last_time_seen, id=None):
        unknown = Unknown(alarm_id, first_time_seen, last_time_seen, id)
        print(f"Unknown created: {str(unknown)}")
        return unknown

    def createOrUpdateUnknown(self, id, alarm_id, first_time_seen, last_time_seen):
        Unknown.create_or_update_unknown(id, alarm_id, first_time_seen, last_time_seen)
        # print(f"Unknown updated: {str(Unknown.get_with_id(id))}")

    def updateAlarmUpdateTime(seld, alarm_id, last_time_seen):
        alarm_updated = Alarm.update_alarm_update_time(alarm_id, last_time_seen)
        # print(f"Alarm updated: {str(alarm_updated)}")

    def updateAlarmStatus(self, alarm_id, status):
        alarm_updated = Alarm.update_alarm_status(alarm_id, status)
        # print(f"Alarm updated: {str(alarm_updated)}")

    def createUnknownFaceEncoding(
        self, unknown_face_id, encoding, img_path=None, id=None
    ):
        unknown_face_encoding = UnknownFaceEncoding(
            unknown_face_id, encoding, img_path, id
        )
        print(f"Unknown Face Encoding created: {str(unknown_face_encoding)}")
        return unknown_face_encoding

    def mv_uknowns_to_knowns(self, alarm_id, camera_id):
        unknowns = Unknown.get_rows_on_alarm_id(alarm_id)
        for unknown in unknowns:
            known_face = KnownFace(camera_id, f"Known_{unknown.id}", unknown.id)
            ids_encodings_img_paths = (
                UnknownFaceEncoding.get_encodings_ids_img_paths_on_unknown_face_id(
                    unknown.id
                )
            )
            Unknown.delete_on_id(unknown.id)
            print(f"Unknown {unknown.id} deleted")
            for enc_id, encoding, img_path in ids_encodings_img_paths:
                known_face_encoding = KnownFaceEncoding(unknown.id, encoding, img_path)
                UnknownFaceEncoding.delete_on_id(enc_id)
                print(f"Unknown Face Encoding {enc_id} is being deleted")
                print(f"Known Face Encoding created: {str(known_face_encoding)}")

    def rm_uknowns_on_alarm_id(self, alarm_id, camera_id):
        unknowns = Unknown.get_rows_on_alarm_id(alarm_id)
        for unknown in unknowns:
            ids_encodings_img_paths = (
                UnknownFaceEncoding.get_encodings_ids_img_paths_on_unknown_face_id(
                    unknown.id
                )
            )
            Unknown.delete_on_id(unknown.id)
            print(f"Unknown {unknown.id} deleted")
            for enc_id, _, _ in ids_encodings_img_paths:
                UnknownFaceEncoding.delete_on_id(enc_id)
                print(f"Unknown Face Encoding {enc_id} is being deleted")

    def get_known_faces_name_encodings(self, camera_id):
        encoding_2_name = {}
        known_faces = KnownFace.get_rows_on_camera_id(camera_id)
        for known_face in known_faces:
            encodings = KnownFaceEncoding.get_encodings_on_known_face_id(known_face.id)
            for encoding in encodings:
                encoding_2_name[tuple(encoding.flatten())] = known_face.display_name

        return {}  # encoding_2_name

    def get_pending_alarm_ids(self, camera_id):
        pendings_alarms = Alarm.get_pending_alarms_rows_on_camera_id(camera_id)
        print(
            f"Found {len(pendings_alarms)} active or pending alarms for camera {camera_id}"
        )
        if not pendings_alarms:
            return []
        alarm_ids = [alarm.id for alarm in pendings_alarms]
        return alarm_ids

    def get_latest_alarm_info(self, camera_id, max_enc_per_person=5):

        pendings_alarms = Alarm.get_pending_alarms_rows_on_camera_id(camera_id)
        active_alarms = Alarm.get_active_alarms_rows_on_camera_id(camera_id)
        alarms = pendings_alarms + active_alarms
        print(f"Found {len(alarms)} active or pending alarms for camera {camera_id}")
        if not alarms:
            return None
        max_start_time = alarms[0].start_date_time
        max_alarm = alarms[0]
        for alarm in alarms:
            if alarm.start_date_time > max_start_time:
                max_start_time = alarm.start_date_time
                max_alarm = alarm

        unknowns = Unknown.get_rows_on_alarm_id(max_alarm.id)
        unknown_people = []
        all_padded_encodings = []
        for unknown in unknowns:
            unknown_encodings = UnknownFaceEncoding.get_encodings_on_unknown_face_id(
                unknown.id
            )
            unknown_encodings = unknown_encodings[:max_enc_per_person]
            unkown_person = UnknownPerson(
                encodings=unknown_encodings,
                first_seen=unknown.first_time_seen,
                snapshots=[None] * len(unknown_encodings),
                max_encodings=max_enc_per_person,
                id=unknown.id,
                alerted=True,
                all_encodings_saved=True,
                all_img_saved=True,
                img_paths=[None] * len(unknown_encodings),
            )
            unknown_people.append(unkown_person)
            padded_encodings = (
                unknown_encodings
                if len(unknown_encodings) == max_enc_per_person
                else unknown_encodings
                + [NULL_ENCODING] * (max_enc_per_person - len(unknown_encodings))
            )
            all_padded_encodings.extend(padded_encodings)
        alert = Alert(
            id=max_alarm.id,
            unknown_ids=set([unknown.id for unknown in unknown_people]),
            unknown_encodings=all_padded_encodings,
            unknowns=unknown_people,
            update_time=max_alarm.update_time,
            start_time=max_alarm.start_date_time,
            status=max_alarm.status,
        )
        return alert


def main():
    print("Starting User Interface...")
    db = DBInterface()

    # # Admin
    # camera_admin = db.createCameraAdmin(
    #     "test_name", "test_surname", "test@gmail.com", "+306999999999"
    # )

    # # Building
    # building = db.createBuilding("Test Building", "123 Test St", "Residential", 2, 101)

    # # Camera
    # camera = db.createCamera(building.id, "test_type", "test_address", "test_desc")

    # # Camera to Admin relation
    # db.relate_camera_admin_to_camera(camera.id, camera_admin.id)

    # # Alert Contact
    # alert_contact = db.createAlertContact(
    #     camera.id,
    #     "test_alert_name",
    #     "test_alert_surname",
    #     "dimitrisatromitara@gmail.com",
    #     "+306999999999",
    # )

    # # Known Faces
    # known_face_1 = db.createKnownFace(camera.id, "dimitris")
    # known_face_1_encodings = db.createKnownFaceEncodings(
    #     known_face_1.id, "data/known_face_images/dimitris/"
    # )
    # known_face_2 = db.createKnownFace(camera.id, "Sak")
    # known_face_2_encodings = db.createKnownFaceEncodings(
    #     known_face_2.id, "data/known_face_images/sak/"
    # )
    # known_face_3 = db.createKnownFace(camera.id, "Mike")
    # known_face_3_encodings = db.createKnownFaceEncodings(
    #     known_face_3.id, "data/known_face_images/mike/"
    # )

    # known_face_4 = db.createKnownFace(0, "Deppy")
    # known_face_4_encodings = db.createKnownFaceEncodings(
    #     known_face_4.id, "data/known_face_images/deppy/"
    # )
    known_face_4 = db.createKnownFace(0, "DIMTEST")
    known_face_4_encodings = db.createKnownFaceEncodings(
        known_face_4.id, "data/known_face_images/dimitris/"
    )

    # Get known faces encodings
    # encoding_2_name = db.get_known_faces_name_encodings(camera_id=0)
    # print("Known Faces Encodings:")
    # for encoding, name in encoding_2_name.items():
    #     print(f"Name: {name}, Encoding: {encoding[:3]}")


if __name__ == "__main__":
    main()
