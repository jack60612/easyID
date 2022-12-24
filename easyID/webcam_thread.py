import sys
import time
from typing import Optional, List

import cv2
import numpy as np
from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QImage

from easyID.common_classes import RecognitionResult
from easyID.settings import WEBCAM_ID, FPS_LIMIT, SIMILARITY_THRESHOLD


# this thread is used to capture frames from the webcam
class VideoThread(QThread):
    updateFrame = Signal(QImage, bool)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.results: List[RecognitionResult] = []
        self.cap = cv2.VideoCapture(WEBCAM_ID)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)  # float `width`
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
        self.frame: Optional[np.ndarray] = None

    def run(self):
        unknown_subjects = False
        while self.cap.isOpened():
            (status, frame_raw) = self.cap.read()
            self.frame = cv2.flip(frame_raw, 1)
            if self.results:
                results = self.results
                for result in results:
                    cv2.rectangle(img=self.frame, pt1=(result.x_min, result.y_min),
                                  pt2=(result.x_max, result.y_max), color=(0, 255, 0), thickness=1)
                    if result.age_low and result.age_high:
                        age = f"Age: {result.age_low} - {result.age_high}"
                        cv2.putText(self.frame, age, (result.x_max, result.y_min + 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                    if result.gender:
                        gender = f"Gender: {result.gender}"
                        cv2.putText(self.frame, gender, (result.x_max, result.y_min + 35),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

                    if result.subject and result.similarity > SIMILARITY_THRESHOLD:
                        subject = f"Subject: {result.subject}"
                        similarity = f"Similarity: {result.similarity}"
                        cv2.putText(self.frame, subject, (result.x_max, result.y_min + 75),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                        cv2.putText(self.frame, similarity, (result.x_max, result.y_min + 95),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                    else:
                        unknown_subjects = True
                        subject = f"No known faces"
                        cv2.putText(self.frame, subject, (result.x_max, result.y_min + 75),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

            color_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
            # Emit signal
            self.updateFrame.emit(img, unknown_subjects)
            unknown_subjects = False
            time.sleep(FPS_LIMIT)
        sys.exit(-1)
