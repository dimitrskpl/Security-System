from utils import (
    get_last_row_id,
    append_dict_to_csv,
    get_with_id,
    get_rows_where,
    generate_id,
    del_rows_where,
)
import numpy as np
import json

KNOWN_FACE_ENCODING_CSV = "data/KnownFaceEncoding.csv"


class KnownFaceEncoding:
    serialization = {
        "encoding": lambda arr: json.dumps(arr.tolist()),
    }

    deserialization = {
        "encoding": lambda s: np.array(json.loads(s)),
    }

    def __init__(
        self,
        known_face_id: int,
        encoding: np.ndarray,
        img_path: str = None,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else generate_id()
        self.known_face_id = known_face_id
        self.encoding = encoding
        self.img_path = img_path

        if save:
            self.save()

    def save(self):
        encoding_str = (
            self.serialization["encoding"](self.encoding)
            if "encoding" in self.serialization
            else str(self.encoding)
        )

        data = {
            "id": self.id,
            "known_face_id": self.known_face_id,
            "encoding": encoding_str,
            "img_path": self.img_path,
        }
        append_dict_to_csv(KNOWN_FACE_ENCODING_CSV, data)

    def __str__(self):
        enc = "encoding" if self.encoding is not None else "None"
        return f"KnownFaceEncoding({self.id}, {self.known_face_id}, {enc}, {self.img_path})"

    @staticmethod
    def get_encodings_on_known_face_id(know_face_id):
        column_2_val = {
            "known_face_id": know_face_id,
        }
        rows = get_rows_where(KNOWN_FACE_ENCODING_CSV, column_2_val, KnownFaceEncoding)
        encodings = [row.encoding for row in rows]
        return encodings

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, KNOWN_FACE_ENCODING_CSV, cls)

    @staticmethod
    def delete_on_id(id: int):
        column_2_val = {
            "id": id,
        }
        del_rows_where(KNOWN_FACE_ENCODING_CSV, column_2_val)
