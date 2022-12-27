import sys
import time
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal

from easyID.common_classes import RecognitionResult
from easyID.settings import ADD_TIMESTAMP, FPS_LIMIT, SIMILARITY_THRESHOLD, WEBCAM_ID


# this thread is used to capture frames from the webcam
class VideoThread(QThread):
    updateFrame = Signal(np.ndarray, bool)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.results: List[RecognitionResult] = []
        self.cap = cv2.VideoCapture(WEBCAM_ID)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame: Optional[np.ndarray] = None

    def run(self):
        unknown_subjects = False
        while self.cap.isOpened():
            (status, frame_raw) = self.cap.read()
            self.frame = cv2.flip(frame_raw, 1)
            if ADD_TIMESTAMP:  # put timestamp on frame
                cv2.putText(
                    img=self.frame,
                    text=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]),
                    org=(20, self.height - 10),
                    fontFace=cv2.FONT_HERSHEY_PLAIN,
                    fontScale=1,
                    color=(255, 255, 255),
                )
            if self.results:
                results = self.results
                for result in results:
                    cv2.rectangle(
                        img=self.frame,
                        pt1=(result.x_min, result.y_min),
                        pt2=(result.x_max, result.y_max),
                        color=(0, 255, 0),
                        thickness=1,
                    )
                    if result.age_low and result.age_high:
                        age = f"Age: {result.age_low} - {result.age_high}"
                        cv2.putText(
                            self.frame,
                            age,
                            (result.x_max, result.y_min + 15),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            1,
                        )
                    if result.gender:
                        gender = f"Gender: {result.gender}"
                        cv2.putText(
                            self.frame,
                            gender,
                            (result.x_max, result.y_min + 35),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            1,
                        )

                    if result.subject and result.similarity > SIMILARITY_THRESHOLD:
                        subject = f"Subject: {result.subject}"
                        similarity = f"Similarity: {result.similarity}"
                        cv2.putText(
                            self.frame,
                            subject,
                            (result.x_max, result.y_min + 75),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            1,
                        )
                        cv2.putText(
                            self.frame,
                            similarity,
                            (result.x_max, result.y_min + 95),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            1,
                        )
                    else:
                        unknown_subjects = True
                        subject = "No known faces"
                        cv2.putText(
                            self.frame,
                            subject,
                            (result.x_max, result.y_min + 75),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            1,
                        )

            # Emit signal / send raw frame to pyqt
            self.updateFrame.emit(self.frame, unknown_subjects)

            unknown_subjects = False
            time.sleep(FPS_LIMIT)
        sys.exit(-1)
