# this thread contacts the CompreFace server and actually does the face recognition
from typing import Any

import cv2
from compreface import CompreFace
from compreface.service import RecognitionService
from PySide6.QtCore import QThread

from easyID.common_classes import process_rec_results
from easyID.settings import CF_OPTIONS
from easyID.webcam_thread import VideoThread


class ProcessingThread(QThread):
    def __init__(self, video_thread: VideoThread, args: Any, parent=None):
        QThread.__init__(self, parent)
        self.video_thread: VideoThread = video_thread

        self.compre_face: CompreFace = CompreFace(
            args.host,
            args.port,
            CF_OPTIONS,
        )
        self.recognition: RecognitionService = self.compre_face.init_face_recognition(args.api_key)

    def run(self):
        while self.video_thread.cap.isOpened():
            if self.video_thread.frame is not None:
                _, im_buf_arr = cv2.imencode(".jpg", self.video_thread.frame)
                byte_im = im_buf_arr.tobytes()
                data = self.recognition.recognize(byte_im)
                self.video_thread.results = process_rec_results(data.get("result"))
