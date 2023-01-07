# this thread contacts the CompreFace server and actually does the face recognition
import time
from threading import Thread
from typing import Any

import cv2
from compreface import CompreFace
from compreface.service import RecognitionService

from easyID.classes.recognition_result import process_rec_results
from easyID.settings import CF_OPTIONS
from easyID.threads.webcam_thread import WebcamThread


class RecognitionThread:
    def __init__(self, webcam_thread: WebcamThread, args: Any) -> None:
        self._stop: bool = False
        self._main_thread: Thread = Thread(target=self.run)

        self._webcam_thread: WebcamThread = webcam_thread
        self.compre_face: CompreFace = CompreFace(
            args.host,
            args.port,
            CF_OPTIONS,
        )
        self.recognition: RecognitionService = self.compre_face.init_face_recognition(args.api_key)

    def start(self) -> None:
        self._main_thread.start()

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        last_frame = None
        while self._webcam_thread.cap.isOpened() and not self._stop:
            if self._webcam_thread.frame is not None and self._webcam_thread.frame is not last_frame:
                last_frame = self._webcam_thread.frame
                _, im_buf_arr = cv2.imencode(".jpg", last_frame)  # convert frame to jpg image
                byte_im = im_buf_arr.tobytes()  # jpg image in bytes
                data = self.recognition.recognize(byte_im)
                self._webcam_thread.results = process_rec_results(data.get("result"))
            else:
                # print("Recognition Thread sleeping for 5ms")
                time.sleep(0.005)  # 5 ms
        # on exit:
        print("Recognition Thread Exited")
