from utils import (
    get_last_row_id,
    append_dict_to_csv,
    get_with_id,
    get_rows_where,
    del_rows_where,
)
import numpy as np
import json

UNKNOWN_FACE_ENCODING_CSV = "data/UnknownFaceEncoding.csv"


class UnknownFaceEncoding:
    serialization = {
        "encoding": lambda arr: json.dumps(arr.tolist()),
    }

    deserialization = {
        "id": str,
        "known_face_id": int,
        "encoding": lambda s: np.array(json.loads(s)),
    }

    def __init__(
        self,
        unknown_face_id: int,
        encoding: np.ndarray,
        img_path: str = None,
        id: int = None,
        save: bool = True,
    ):
        self.id = id if id is not None else get_last_row_id(KNOWN_FACE_ENCODING_CSV) + 1
        self.unknown_face_id = unknown_face_id
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
            "unknown_face_id": self.unknown_face_id,
            "encoding": encoding_str,
            "img_path": self.img_path,
        }
        append_dict_to_csv(UNKNOWN_FACE_ENCODING_CSV, data)

    def __str__(self):
        enc = "encoding" if self.encoding is not None else "None"
        return f"UnknownFaceEncoding({self.id}, {self.unknown_face_id}, {enc}, {self.img_path})"

    @staticmethod
    def get_encodings_on_unknown_face_id(unknown_face_id):
        column_2_val = {
            "unknown_face_id": unknown_face_id,
        }
        rows = get_rows_where(
            UNKNOWN_FACE_ENCODING_CSV, column_2_val, UnknownFaceEncoding
        )
        encodings = [row.encoding for row in rows]
        return encodings

    @staticmethod
    def get_encodings_ids_img_paths_on_unknown_face_id(unknown_face_id):
        column_2_val = {
            "unknown_face_id": unknown_face_id,
        }
        rows = get_rows_where(
            UNKNOWN_FACE_ENCODING_CSV, column_2_val, UnknownFaceEncoding
        )
        encodings_img_paths = [(row.id, row.encoding, row.img_path) for row in rows]
        return encodings_img_paths

    @staticmethod
    def get_with_id(cls, id: int):
        return get_with_id(id, UNKNOWN_FACE_ENCODING_CSV, cls)

    @staticmethod
    def delete_on_id(id: int):
        column_2_val = {
            "id": id,
        }
        del_rows_where(UNKNOWN_FACE_ENCODING_CSV, column_2_val)
