import cv2


class MotionDetector:
    def __init__(self, sensitivity=5000):
        self.motion_background = None
        self.motion_sensitivity = sensitivity

    def detect_motion(self, frame):
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
