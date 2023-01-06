# this thread contacts the CompreFace server and actually does the face recognition
from threading import Thread
from typing import Any

import cv2
from compreface import CompreFace
from compreface.service import RecognitionService

from easyID.common_classes import process_rec_results
from easyID.settings import CF_OPTIONS
from easyID.webcam_thread import VideoThread


class ProcessingThread:
    def __init__(self, video_thread: VideoThread, args: Any) -> None:
        self.video_thread: VideoThread = video_thread  # QThread
        self._stop: bool = False

        self.compre_face: CompreFace = CompreFace(
            args.host,
            args.port,
            CF_OPTIONS,
        )
        self.recognition: RecognitionService = self.compre_face.init_face_recognition(args.api_key)
        self._main_thread: Thread = Thread(target=self.run)

    def start(self) -> None:
        self._main_thread.start()

    def terminate(self) -> None:
        self._stop = True

    def run(self):
        while self.video_thread.cap.isOpened() and not self._stop:
            if self.video_thread.frame is not None:
                _, im_buf_arr = cv2.imencode(".jpg", self.video_thread.frame)
                byte_im = im_buf_arr.tobytes()
                data = self.recognition.recognize(byte_im)
                self.video_thread.results = process_rec_results(data.get("result"))
        # on exit:
        self.video_thread.results = []
        print("Processing Thread Exited")
