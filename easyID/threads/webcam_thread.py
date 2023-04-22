# this thread contacts the CompreFace server and actually does the face recognition
from threading import Thread
from typing import List, Optional

import cv2
import numpy as np

from easyID.classes.recognition_result import RecognitionResult
from easyID.settings import WEBCAM_HEIGHT, WEBCAM_ID, WEBCAM_WIDTH


class WebcamThread:
    def __init__(self) -> None:
        self._stop: bool = False
        self._main_thread: Thread = Thread(target=self.run)

        self.cap = cv2.VideoCapture(WEBCAM_ID)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        # override the default resolution
        if WEBCAM_WIDTH is not None and WEBCAM_HEIGHT is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.frame: Optional[np.ndarray] = None
        self.results: List[RecognitionResult] = []  # we have this here for simplicity, but it could be moved.

    def start(self) -> None:
        self._main_thread.start()

    def stop(self) -> None:
        self._stop = True
        self._main_thread.join()  # wait for webcam thread to stop
        self.cap.release()

    def run(self) -> None:
        while self.cap.isOpened() and not self._stop:
            (status, frame_raw) = self.cap.read()
            self.frame = cv2.flip(frame_raw, 1)
            # print("frame updated")
        # on exit:
        self.frame = None
        self.results = []
        print("Webcam Thread Exited")
