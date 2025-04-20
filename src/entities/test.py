import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from camera import Camera


def test_camera_save_and_load():
    print("📷 Creating new camera record...")
    cam = Camera(
        building_id=1,
        type="Indoor",
        camera_address="192.168.1.10",
        usage_desc="Main entrance",
    )
    print("✅ Camera created:", cam)

    print(f"🔍 Trying to reload camera with id={cam.id} from CSV...")
    loaded = Camera.get_with_id(cam.id)
    print("📦 Loaded camera:", loaded)

    assert loaded.id == cam.id
    assert loaded.camera_address == cam.camera_address
    assert loaded.usage_desc == cam.usage_desc
    print("✅ Test passed!")
    print(str(loaded))


if __name__ == "__main__":
    test_camera_save_and_load()
