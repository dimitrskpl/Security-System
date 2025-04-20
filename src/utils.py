import uuid
import face_recognition
import csv
import cv2
import numpy as np

NULL_ENCODING = np.zeros((128,), dtype=np.float64)


# def get_face_encodings(image_path):
#     image = face_recognition.load_image_file(image_path)
#     encodings = face_recognition.face_encodings(image)
#     if encodings:
#         return encodings[0]
#     return None


def get_face_encodings(image_path):
    try:
        print(f"🖼️ Loading image from: {image_path}")
        image = face_recognition.load_image_file(image_path)
        print(f"✅ Image loaded successfully. Shape: {image.shape}")
        encodings = face_recognition.face_encodings(image)
        if encodings:
            print(f"✅ Found {len(encodings)} face(s) in {image_path}")
            return encodings[0]
        else:
            print(f"⚠️ No face encodings found in {image_path}")
    except Exception as e:
        print(f"❌ Error during face encoding for {image_path}: {e}")

    return None


import threading


class FaceRecognition:
    def __init__(self):
        self.lock = threading.Lock()

    def get_face_encodings(self, image_path):
        try:
            image = face_recognition.load_image_file(image_path)
            with self.lock:
                encodings = face_recognition.face_encodings(image)
            if encodings:
                return encodings[0]
            else:
                print(f"⚠️ No face encodings found in {image_path}")
        except Exception as e:
            print(f"❌ Error during face encoding for {image_path}: {e}")

        return None

    def get_face_loc_encodings(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        with self.lock:
            face_locations = face_recognition.face_locations(rgb_frame)
            encodings = []
            for face_location in face_locations:
                enc = face_recognition.face_encodings(rgb_frame, [face_location])
                if enc:
                    encodings.append(enc[0])
        return face_locations, encodings

    def get_best_distance_idx(self, encodings, face_encoding):
        face_distances = face_recognition.face_distance(encodings, face_encoding)

        if len(face_distances) == 0:
            return None, None

        best_match_index = face_distances.argmin()
        best_distance = face_distances[best_match_index]

        return best_match_index, best_distance


def generate_id():
    return str(uuid.uuid4())[:8]


# def append_dict_to_csv(file_path, data_dict):
#     if not csv_exists(file_path):
#         create_csv(file_path, data_dict.keys())

#     with open(file_path, "a") as f:
#         f.write(",".join([str(value) for value in data_dict.values()]) + "\n")


def create_csv_if_not_exists(file_path, headers):
    if not csv_exists(file_path):
        create_csv(file_path, headers)


def append_dict_to_csv(file_path, data_dict):
    if not csv_exists(file_path):
        create_csv(file_path, data_dict.keys())

    with open(file_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data_dict.keys())
        writer.writerow(data_dict)


def csv_exists(file_path):
    try:
        with open(file_path, "r") as f:
            return True
    except FileNotFoundError:
        return False


def create_csv(file_path, headers):
    with open(file_path, "w") as f:
        f.write(",".join(headers) + "\n")


def get_last_row_id(file_path):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_row = lines[-1]
                last_row_id = last_row.split(",")[0]
                return last_row_id
            else:
                return 0
    except FileNotFoundError:
        return -1


def get_with_id(id: int, file_path: str, class_type):
    with open(file_path, "r") as f:
        lines = f.readlines()
        if not lines:
            return None

        headers = lines[0].strip().split(",")
        for line in lines[1:]:
            row = line.strip().split(",")
            row_dict = dict(zip(headers, row))

            if row_dict["id"] == id:
                deserialized = {}
                for key, value in row_dict.items():
                    if key in class_type.deserialization:
                        deserialized[key] = class_type.deserialization[key](value)
                    else:
                        deserialized[key] = value  # assume string if not specified

                return class_type(**deserialized, save=False)


def get_rows_where(file_path: str, column_2_val: dict, class_type=None):
    results = []
    try:
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                match = all(
                    str(row.get(col)) == str(val) for col, val in column_2_val.items()
                )
                if match:
                    if class_type:
                        deserialized = {}
                        for key, value in row.items():
                            if (
                                hasattr(class_type, "deserialization")
                                and key in class_type.deserialization
                            ):
                                deserialized[key] = class_type.deserialization[key](
                                    value
                                )
                            else:
                                deserialized[key] = value
                        results.append(class_type(**deserialized, save=False))
                    else:
                        results.append(row)
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
    return results


def update_row_by_id(file_path, row_id, updated_data_dict):
    try:
        with open(file_path, "r") as f:
            reader = list(csv.DictReader(f))
            headers = reader[0].keys() if reader else updated_data_dict.keys()

        updated = False
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in reader:
                if str(row.get("id")) == str(row_id):
                    row.update(updated_data_dict)
                    updated = True
                writer.writerow(row)

        return updated
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
        return False


def create_or_update_row(file_path, data_dict, class_type):
    row_id = str(data_dict.get("id"))
    if row_id is None:
        raise ValueError("data_dict must contain 'id' key for update or create logic.")

    if csv_exists(file_path):
        existing = get_with_id(row_id, file_path, class_type)
        if existing:
            update_row_by_id(file_path, row_id, data_dict)
            return

    append_dict_to_csv(file_path, data_dict)


def save_snapshot(frame, filename):
    cv2.imwrite(filename, frame)
    print(f"✅ Snapshot saved: {filename}")


def del_rows_where(file_path: str, column_2_val: dict) -> int:
    """
    Deletes rows from a CSV file where all specified column values match.

    Returns:
        int: Number of rows deleted.
    """
    try:
        with open(file_path, "r") as f:
            reader = list(csv.DictReader(f))
            if not reader:
                return 0
            headers = reader[0].keys()

        # Filter rows that DO NOT match (we keep these)
        remaining_rows = []
        deleted_count = 0
        for row in reader:
            match = all(
                str(row.get(col)) == str(val) for col, val in column_2_val.items()
            )
            if not match:
                remaining_rows.append(row)
            else:
                deleted_count += 1

        # Write back only non-deleted rows
        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(remaining_rows)

        return deleted_count

    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
        return 0
